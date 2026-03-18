"""
Image Ingestion Utility

Handles image upload to S3 and extraction of debate-relevant context from images.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

import boto3
from botocore.exceptions import ClientError, SSLError
import urllib3

from utils.bedrock_client import get_bedrock_client

ALLOWED_MEDIA_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
}


def _normalize_media_type(media_type: str) -> str:
    if media_type == "image/jpg":
        return "image/jpeg"
    return media_type


def _safe_file_name(name: str) -> str:
    return name.replace(" ", "_").replace("..", "")


def _should_disable_s3_ssl_verification() -> bool:
    value = os.getenv("S3_DISABLE_SSL_VERIFICATION", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _create_s3_client():
    if _should_disable_s3_ssl_verification():
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return boto3.client("s3", verify=False)
    return boto3.client("s3")


def upload_images_to_s3(
    uploaded_files: List[Any],
    bucket_name: str,
    topic: str,
) -> List[Dict[str, Any]]:
    """
    Upload Streamlit uploaded image files to S3.

    Returns a list of objects with keys: key, s3_uri, media_type, file_name.
    """
    s3 = _create_s3_client()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    image_prefix = os.getenv("S3_IMAGE_PREFIX", "debate-images").strip("/") or "debate-images"
    prefix = f"{image_prefix}/{timestamp}"

    uploaded_objects: List[Dict[str, Any]] = []

    for file in uploaded_files:
        media_type = _normalize_media_type(file.type or "")
        if media_type not in ALLOWED_MEDIA_TYPES:
            continue

        file_name = _safe_file_name(file.name)
        key = f"{prefix}/{file_name}"

        file_bytes = file.getvalue()
        s3.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=file_bytes,
            ContentType=media_type,
            Metadata={
                "topic": topic[:200],
            },
        )

        uploaded_objects.append(
            {
                "key": key,
                "s3_uri": f"s3://{bucket_name}/{key}",
                "media_type": media_type,
                "file_name": file_name,
                # Keep in-memory bytes as fallback in environments with strict SSL interception.
                "bytes": file_bytes,
            }
        )

    return uploaded_objects


def analyze_images_from_s3(
    bucket_name: str,
    uploaded_objects: List[Dict[str, Any]],
    topic: str,
) -> Tuple[str, List[str]]:
    """
    Read uploaded images from S3 and produce a consolidated analysis summary.

    Returns tuple: (summary_text, list_of_s3_uris)
    """
    if not uploaded_objects:
        return "", []

    s3 = _create_s3_client()
    bedrock = get_bedrock_client()

    per_image_notes: List[str] = []
    s3_uris: List[str] = []

    for obj in uploaded_objects:
        key = obj["key"]
        media_type = obj["media_type"]
        s3_uris.append(obj["s3_uri"])

        try:
            response = s3.get_object(Bucket=bucket_name, Key=key)
            image_bytes = response["Body"].read()
        except SSLError:
            # Fallback when local trust store cannot validate S3 certificate chain.
            if obj.get("bytes"):
                image_bytes = obj["bytes"]
            else:
                raise Exception(
                    "S3 read-back failed due to SSL certificate validation. "
                    "Configure CA bundle (AWS_CA_BUNDLE) or update system certs."
                )
        except Exception as e:
            if obj.get("bytes"):
                image_bytes = obj["bytes"]
            else:
                raise Exception(f"Failed to read image from S3: {str(e)}")

        prompt = (
            "Analyze this image for a technical debate. "
            f"Debate topic: {topic}\n"
            "Extract only concrete, observable details and infer likely technical implications. "
            "Return 5-8 concise bullet points covering architecture, performance, and security signals when relevant."
        )

        image_note = bedrock.generate_multimodal_response(
            prompt=prompt,
            images=[{"bytes": image_bytes, "media_type": media_type}],
            system_prompt=(
                "You are a technical analyst. Do not hallucinate hidden details. "
                "If uncertain, explicitly say uncertain."
            ),
            max_tokens=900,
            temperature=0.2,
        )

        per_image_notes.append(f"Image: {obj['file_name']}\n{image_note}")

    combined_prompt = (
        "You are consolidating multiple image analyses for a technical debate.\n"
        f"Topic: {topic}\n\n"
        "Per-image analyses:\n"
        + "\n\n".join(per_image_notes)
        + "\n\nCreate a single concise context section with:\n"
        "1) Key factual observations\n"
        "2) Debate-relevant assumptions (labeled assumptions)\n"
        "3) How these observations may affect architecture, performance, and security arguments"
    )

    combined_summary = bedrock.generate_response(
        combined_prompt,
        system_prompt="You synthesize technical context for structured debates.",
        max_tokens=1200,
        temperature=0.2,
    )

    return combined_summary, s3_uris


def upload_and_process_images(
    uploaded_files: List[Any],
    topic: str,
    bucket_name: str,
) -> Tuple[str, List[str]]:
    """
    Upload images to S3 and return processed image context + S3 URIs.
    """
    if not bucket_name:
        bucket_name = (
            os.getenv("S3_IMAGE_BUCKET_NAME")
            or os.getenv("S3_BUCKET_NAME")
            or os.getenv("AWS_S3_BUCKET")
            or ""
        )

    if not bucket_name:
        raise ValueError(
            "S3 bucket is required for image ingestion. Set S3_IMAGE_BUCKET_NAME."
        )

    try:
        uploaded_objects = upload_images_to_s3(uploaded_files, bucket_name, topic)
        if not uploaded_objects:
            return "", []
        return analyze_images_from_s3(bucket_name, uploaded_objects, topic)
    except ClientError as e:
        raise Exception(f"S3 image ingestion failed: {str(e)}")

"""
code/fact_extractor/__init__.py - Facade for fact reconciliation.
Executes image extraction in serial 3-image batches and message updates in serial 25-msg batches,
inserting a 2-second delay between batches.
"""

import sys
from pathlib import Path

code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from typing import Dict, List, Tuple
from models import FinancialEvent, Message

try:
    from .image_extractor import resolve_image_amounts_in_batches
    from .message_processor import apply_message_updates_in_batches
except ImportError:
    from image_extractor import resolve_image_amounts_in_batches
    from message_processor import apply_message_updates_in_batches


def reconcile_financial_facts(
    events_by_user: Dict[str, List[FinancialEvent]],
    messages: List[Message],
    images_map: Dict[str, str],
    media_dir: Path,
    image_batch_size: int = 3,
    message_batch_size: int = 25,
    batch_delay_sec: float = 2.0,
) -> Tuple[int, int]:
    """
    Unified serial batch fact extractor pipeline:
    1. Extracts missing amounts in serial batches of 3 images with 2s delay.
    2. Applies message rule adjustments in serial batches of 25 messages with 2s delay.
    """
    resolved_images = resolve_image_amounts_in_batches(
        events_by_user, images_map, media_dir, batch_size=image_batch_size, batch_delay_sec=batch_delay_sec
    )
    modified_messages = apply_message_updates_in_batches(
        events_by_user, messages, batch_size=message_batch_size, batch_delay_sec=batch_delay_sec
    )
    return resolved_images, modified_messages


if __name__ == "__main__":
    from loaders import load_events, load_images_map, load_messages

    base_dir = code_dir.parent / "dataset"
    events = load_events(str(base_dir / "financial_events.csv"))
    images = load_images_map(str(base_dir / "images.csv"))
    messages = load_messages(str(base_dir / "messages.csv"))
    media = base_dir / "media" / "images"

    resolved_img, mod_msg = reconcile_financial_facts(events, messages, images, media)
    print(f"\nFact Reconciliation Complete: Resolved {resolved_img} images, updated {mod_msg} message events.")

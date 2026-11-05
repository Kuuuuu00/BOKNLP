"""Shared constants for the P2 vote/boilerplate review workbook (10b_make_vote_review_xlsx.py, 10c_merge_vote_review.py).
Guide C4: reviewer_judgment is ok|missed|over, restricted per audit row type.
"""
ALLOWED = {
    "flagged_vote": ("ok", "over"),
    "candidate_miss": ("ok", "missed"),
    "boilerplate": ("ok", "over"),
}
KEY = ["meeting_date", "sent_id", "type"]  # 18 sentences are both candidate_miss and boilerplate, so type is part of the key

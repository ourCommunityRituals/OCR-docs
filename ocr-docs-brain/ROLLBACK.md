# ROLLBACK

Undo last commit:
  cd ~/dev/ourCommunityRituals/OCR-docs
  git revert HEAD --no-edit
  git push origin main

Verify after rollback:
  py ocr-docs-brain/tests/run_all.py

# Metadata and task progress

The current task API returns a normalized task structure:
- task id, source URL, selected engine and lifecycle status
- video/audio progress percentages from yt-dlp hooks
- gallery file count from gallery-dl
- final output filename, size, file count and download endpoint
- error details for failed or cancelled tasks

The schema is represented by server/kirindl_server/models.py and server/kirindl_server/jobs.py.

A dedicated metadata/format-inspection endpoint has not been implemented yet. The current first working flow starts the selected download task directly.

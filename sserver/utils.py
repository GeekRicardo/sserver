def get_media_type(file_extension: str, direct_download: str = "") -> str:
    # pylint: disable=too-many-return-statements
    if direct_download == "1":
        return "application/octet-stream", True
    if file_extension in ["jpg", "jpeg"]:
        return "image/jpeg", False
    if "png" == file_extension:
        return "image/png", False
    if "txt" == file_extension:
        return "text/plain", False
    if "pdf" == file_extension:
        return "application/pdf", False
    if "json" == file_extension:
        return "application/json", False
    if "gif" == file_extension:
        return "image/gif", False
    if file_extension in ["js", "mjs"]:
        return "application/javascript", False
    if file_extension == "html":
        return "text/html", False
    if file_extension == "css":
        return "text/css", False
    if "xml" == file_extension:
        return "application/xml", False
    if file_extension == "mp4":
        return "video/mp4", False
    if "mp3" == file_extension:
        return "audio/mpeg", False
    if "wav" == file_extension:
        return "audio/wave", False
    if "ogg" == file_extension:
        return "application/ogg", False
    if file_extension in ["ico", "cur"]:
        return "image/x-icon", False
    return "application/octet-stream", True
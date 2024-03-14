def get_media_type(file_extension: str, direct_download: str = "") -> str:
    # pylint: disable=too-many-return-statements
    if direct_download == "1":
        return "application/octet-stream"
    if file_extension in ["jpg", "jpeg"]:
        return "image/jpeg"
    if "png" == file_extension:
        return "image/png"
    if "txt" == file_extension:
        return "text/plain"
    if "pdf" == file_extension:
        return "application/pdf"
    if "json" == file_extension:
        return "application/json"
    if "gif" == file_extension:
        return "image/gif"
    if file_extension in ["js", "mjs"]:
        return "application/javascript"
    if file_extension == "html":
        return "text/html"
    if file_extension == "css":
        return "text/css"
    if "xml" == file_extension:
        return "application/xml"
    if file_extension == "mp4":
        return "video/mp4"
    if "mp3" == file_extension:
        return "audio/mpeg"
    if "wav" == file_extension:
        return "audio/wave"
    if "ogg" == file_extension:
        return "application/ogg"
    if file_extension in ["ico", "cur"]:
        return "image/x-icon"
    return "application/octet-stream"
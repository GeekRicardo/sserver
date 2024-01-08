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
    return "application/octet-stream"
def extract_marker_type(marker_type: str) -> str:
    """
    Extracts the marker type from the marker type string.
    """
    return marker_type.removesuffix("-start").removesuffix("-end")

"""Tag compression by merging consecutive identical operations."""


class Compressor:
    """Compresses tag strings by merging consecutive identical tags."""

    def compress_tags(self, tags: list[str]) -> str:
        """Compresses a tag string by merging consecutive identical tags."""
        if not tags:
            return ""

        compressed = []
        count = 1
        prev_tag = tags[0]

        for tag in tags[1:]:
            if tag == prev_tag:
                count += 1
            else:
                compressed.append(f"{prev_tag}*" if count > 1 else prev_tag)
                prev_tag = tag
                count = 1

        compressed.append(f"{prev_tag}*" if count > 1 else prev_tag)
        return "".join(compressed)

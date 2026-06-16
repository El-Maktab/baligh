"""Tag compression by merging consecutive identical operations."""


class Compressor:
    """Compresses tag strings by merging consecutive identical tags."""

    INSERT_REPLACE_LABEL_INDEX = 3  # I_[LABEL]

    def _collect_labels(self, tags: list[str], start: int, count: int) -> str:
        label_chars = []
        for i in range(start, start + count):
            match = tags[i].split("_")
            if len(match) > 1:
                label_chars.append(match[1].strip("[]"))
        return "".join(label_chars)

    def compress_tags(self, tags: list[str]) -> str:
        """Compresses a tag string by merging consecutive identical tags."""
        if not tags:
            return ""

        count = 1
        compressed = []
        prev_tag = tags[0]
        start = 0

        for i, tag in enumerate(tags[1:], start=1):
            if tag[0] == prev_tag[0]:
                count += 1
            else:
                compressed.append(self._format_run(prev_tag, tags, start, count))
                prev_tag = tag
                start = i
                count = 1

        compressed.append(self._format_run(prev_tag, tags, start, count))
        return "".join(compressed)

    def _format_run(self, prev_tag, tags, start, count):
        tag_type = prev_tag[0]
        if tag_type in ("I", "R"):
            if count > 1:
                labels = self._collect_labels(tags, start, count)
                return f"{tag_type}_[{labels}]"
            return prev_tag
        else:
            return f"{prev_tag}{count}" if count > 1 else prev_tag

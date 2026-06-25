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

    def compress_tags(self, tags: list[str]) -> tuple[str, str]:
        """Compresses a tag string using both compression variants.

        Returns:
            A tuple of (count_compressed, star_compressed) strings.
        """
        if not tags:
            return ("", "")

        count = 1
        compressed_count = []
        compressed_star = []
        prev_tag = tags[0]
        start = 0

        for i, tag in enumerate(tags[1:], start=1):
            if tag[0] == prev_tag[0]:
                count += 1
            else:
                compressed_count.append(
                    self._format_run_count(prev_tag, tags, start, count)
                )
                compressed_star.append(
                    self._format_run_star(prev_tag, tags, start, count)
                )
                prev_tag = tag
                start = i
                count = 1

        compressed_count.append(
            self._format_run_count(prev_tag, tags, start, count)
        )
        compressed_star.append(
            self._format_run_star(prev_tag, tags, start, count)
        )
        return ("".join(compressed_count), "".join(compressed_star))

    def _format_run_count(self, prev_tag, tags, start, count):
        tag_type = prev_tag[0]
        if tag_type in ("I", "R"):
            if count > 1:
                labels = self._collect_labels(tags, start, count)
                return f"{tag_type}_[{labels}]"
            return prev_tag
        else:
            return f"{prev_tag}{count}" if count > 1 else prev_tag

    def _format_run_star(self, prev_tag, tags, start, count):
        tag_type = prev_tag[0]
        if tag_type in ("I", "R"):
            if count > 1:
                return f"{tag_type}_[c*]"
            else:
                return prev_tag
        else:
            return f"{tag_type}*" if count > 1 else prev_tag

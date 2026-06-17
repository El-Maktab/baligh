"""Tag compression by merging consecutive identical operations."""


class Compressor:
    """Compresses tag strings by merging consecutive identical tags."""

    INSERT_REPLACE_LABEL_INDEX = 3  # I_[LABEL]

    def get_tags(self, prev_tag, tag, cursor, count):
        """Extracts the tag.

        Args:
            prev_tag: Previous tag string.
            tag: Current tag string.
            cursor: Current cursor position.
            count: Count of consecutive identical tags.

        Returns:
            tag string.
        """
        tag_type = prev_tag[0]
        if tag_type == "I" or tag_type == "R":
            label_slice = tag[cursor - count : cursor - 1][
                self.INSERT_REPLACE_LABEL_INDEX
            ]
            return f"{prev_tag}_[{label_slice.join('')}]" if count > 1 else prev_tag
        else:
            return f"{prev_tag}{count}" if count > 1 else prev_tag

    def compress_tags(self, tags: list[str]) -> str:
        """Compresses a tag string by merging consecutive identical tags."""
        if not tags:
            return ""

        count = 1
        cursor = 1
        compressed = []
        prev_tag = tags[0]

        for tag in tags[1:]:
            if tag[0] == prev_tag[0]:
                count += 1
            else:
                compressed.append(self.get_tags(prev_tag, tag, cursor, count))
                prev_tag = tag
                count = 1
            cursor += 1

        compressed.append(self.get_tags(prev_tag, tag, cursor, count))
        return "".join(compressed)

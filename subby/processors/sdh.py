from __future__ import annotations

import copy
import re

from subby import regex as Regex
from subby.processors.base import BaseProcessor
from subby.subripfile import SubRipFile


class SDHStripper(BaseProcessor):
    """Processor removing hard-of-hearing descriptions from subtitles"""

    def __init__(self, extra_regexes: list[str] | None = None):
        self.extra_regexes = [
            re.compile(regex, re.MULTILINE)
            for regex in extra_regexes or []
        ]

    def process(self, srt):
        stripped = [line for line in copy.deepcopy(srt)]
        stripped = self._clean_full_line_descriptions(stripped)
        stripped = self._clean_new_line_descriptions(stripped)
        stripped = self._clean_inline_descriptions(stripped)
        stripped = self._clean_speaker_names(stripped)
        stripped = self._strip_notes(stripped)
        stripped = self._run_extra_regexes(stripped)

        stripped = SubRipFile([line for line in stripped if line.text])
        stripped.clean_indexes()

        return stripped, stripped != srt

    def _clean_full_line_descriptions(self, srt):
        """Removes full line descriptions"""
        for line in srt:
            text = self._strip_tags(line.text)
            for regex in (Regex.FULL_LINE_DESCIRPTION_BRACKET, Regex.FULL_LINE_DESCIRPTION_PARENTHESES):
                text = re.sub(regex, r'', text, flags=re.M).strip()

            if not text:
                continue

            yield line

    def _clean_new_line_descriptions(self, srt):
        """Removes line descriptions taking up an entire line break"""
        for line in srt:
            position = re.match(Regex.POSITION_TAGS, line.text.strip())
            for regex in (Regex.NEW_LINE_DESCRIPTION_BRACKET, Regex.NEW_LINE_DESCRIPTION_PARENTHESES):
                line.text = re.sub(regex, r'', line.text, flags=re.M).strip()

            # Restore position, if it has been removed with the description
            if position and position[0] not in line.text:
                line.text = position[0] + line.text

            yield line

    def _clean_inline_descriptions(self, srt):
        """Removes inline"""
        for line in srt:
            line.text = re.sub(Regex.FRONT_DESCRIPTION_BRACKET, r'\8', line.text, flags=re.M)
            line.text = re.sub(Regex.FRONT_DESCRIPTION_PARENTHESES, r'\1', line.text, flags=re.M)
            for regex in (
                Regex.END_DESCRIPTION_BRACKET,
                Regex.END_DESCRIPTION_PARENTHESES,
                Regex.INLINE_DESCRIPTION
            ):
                line.text = re.sub(regex, r'', line.text, flags=re.M)
            line.text = line.text.strip()
            yield line

    def _clean_speaker_names(self, srt):
        """Removes speaker names"""
        for line in srt:
            # Retain frontal tags/hyphens
            for regex in (Regex.SPEAKER_PARENTHESES, Regex.SPEAKER):
                line.text = re.sub(regex, r'\2', line.text, flags=re.M).strip()
            yield line

    def _strip_notes(self, srt):
        """Removes lines with just musical notes"""
        for line in srt:
            if re.match(r'^♪+$', re.sub(r'\s*', r'', self._strip_tags(line.text).strip())):
                continue

            yield line

    def _run_extra_regexes(self, srt):
        """Runs extra regexes provided by user"""
        for line in srt:
            for regex in self.extra_regexes:
                line.text = re.sub(regex, r'', line.text)
            yield line

    @staticmethod
    def _strip_tags(text: str) -> str:
        return re.sub(Regex.TAGS, r'', text)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

from inspect import getdoc as multiline
from refinery.lib.patterns import indicators, formats

from .. import TestBase


class TestIndicators(TestBase):

    def test_ipv4_too_large_ocets(self):
        self.assertFalse(re.fullmatch(str(indicators.ipv4), '127.0.0.288'))

    def test_ipv4_almost_too_large_ocet(self):
        self.assertTrue(re.fullmatch(str(indicators.ipv4), '13.203.240.255'))


class TestFormats(TestBase):

    def test_ps1str_here_string_match(self):
        @multiline
        class here_string:
            """
            $page = [XML] @"
            <command:command xmlns:maml="http://schemas.microsoft.com/maml/2004/10"
            xmlns:command="http://schemas.microsoft.com/maml/dev/command/2004/10"
            xmlns:dev="http://schemas.microsoft.com/maml/dev/2004/10">
            <command:details>
                    <command:name>
                        Format-Table
                    </command:name>
                    <maml:description>
                        <maml:para>Formats the output as a table.</maml:para>
                    </maml:description>
                    <command:verb>format</command:verb>
                    <command:noun>table</command:noun>
                    <dev:version></dev:version>
            </command:details>
            ...
            </command:command>
            "@
            """

        match = re.search(str(formats.ps1str), here_string, flags=re.DOTALL)
        data = match.group(0)[2:-2].strip()
        self.assertTrue(bool(match), 'string not found')
        self.assertTrue(data.startswith('<command:command'))
        self.assertTrue(data.endswith('</command:command>'))

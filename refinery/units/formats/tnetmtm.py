#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
from enum import IntEnum
from typing import Optional, Dict, Iterator, Union

from refinery import Unit
from refinery.units import Arg


class OutputType(IntEnum):
    payloads = 1
    header_names = 2
    header_value = 3


class tnetmtm(Unit):
    """
    Parses out payloads from tnetstring files generated by mitmproxy. The unit is also able to populate HTTP headers as
    meta variables or emitting header values instead of actual payloads.
    """

    def __init__(
            self,
            headers_as_meta_vars: Arg.Switch('--populate-headers', '-p'),
            list_header_names: Arg.Switch('--list-header-names', '-l'),
            header_filter: Arg('--header-filter', '-f'),
    ):
        ...

    @Unit.Requires('mitmproxy')
    def _tnetstring():
        from mitmproxy.io import tnetstring
        return tnetstring

    @staticmethod
    def _generate_errors(log_line: Dict) -> Iterator[str]:
        def _extract_error(d: Optional[Dict]) -> Optional[str]:
            return ((d or {}).get('error') or {}).get('msg')

        proxy_error = _extract_error(log_line.get('client_conn'))
        if proxy_error:
            yield proxy_error
        error = _extract_error(log_line)
        if error:
            yield error
        return error

    def _default_meta_vars(self, log_line, request: Dict, response: Dict) -> Dict[str, Union[str, int]]:
        ret = {
            'request_method': request.get('method').decode('utf-8'),
            'request_scheme': request.get('scheme').decode('utf-8'),
            'request_host': request.get('host'),
            'request_query_string': request.get('path').decode('utf-8'),
            'request_header_count': len(request.get('headers', [])),
            'response_status_code': response.get('status_code'),
            'response_header_count': len(response.get('headers', [])),
        }
        for num, error in enumerate(self._generate_errors(log_line)):
            ret[f'error_{num}'] = error
        request_http_version = request.get('http_version')
        if request_http_version:
            ret['request_http_version'] = request_http_version.decode('utf-8')
        response_http_version = response.get('http_version')
        if response_http_version:
            ret['response_http_version'] = response_http_version.decode('utf-8')
        return ret

    @staticmethod
    def _output_type(args) -> OutputType:
        if args.list_header_names:
            return OutputType.header_names

        if args.header_filter:
            return OutputType.header_value

        return OutputType.payloads

    def process(self, data: bytearray):
        args = self.args
        tnetstring = self._tnetstring
        output_type = self._output_type(args)

        with io.BytesIO(data) as fp:
            while True:
                try:
                    log_line = tnetstring.load(fp)
                    request = log_line.get('request') or {}
                    response = log_line.get('response') or {}
                    labels = {} if args.headers_as_meta_vars else self._default_meta_vars(log_line, request, response)
                    for header_name, header_value in request.get('headers', []) + response.get('headers', []):
                        if output_type == OutputType.header_names:
                            yield header_name

                        if output_type == OutputType.header_value:
                            if header_name == args.header_filter:
                                yield header_value

                        if args.headers_as_meta_vars:
                            labels[header_name.decode('utf-8').replace('-', '')] = header_value

                    if output_type == OutputType.payloads:
                        yield self.labelled(response.get('content'), **labels)
                except ValueError:
                    break
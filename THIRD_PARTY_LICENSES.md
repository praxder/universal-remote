# Third-Party Licenses

`universal-remote` bundles the third-party Python packages listed below (its
runtime dependencies and their transitive closure). Each remains under its own
license, held by its respective copyright holders. Development-only tooling
(pytest, ruff, PyInstaller, semantic-release, …) is excluded because it is not
distributed with the app.

## Regenerating

This file is generated from the locked runtime dependencies. Regenerate it
whenever the runtime dependencies change:

```sh
uv export --no-dev --no-emit-project --format requirements-txt > /tmp/reqs.txt
uv venv /tmp/rtenv
uv pip install --python /tmp/rtenv/bin/python -r /tmp/reqs.txt pip-licenses
/tmp/rtenv/bin/pip-licenses --format=markdown --with-urls \
  --ignore-packages pip-licenses PTable prettytable wcwidth
```

Paste the resulting table below the heading that follows.

## Packages

| Name                       | Version   | License                              | URL                                                                  |
|----------------------------|-----------|--------------------------------------|----------------------------------------------------------------------|
| Pygments                   | 2.20.0    | BSD-2-Clause                         | https://pygments.org                                                 |
| adb_shell                  | 0.4.4     | Apache Software License              | https://github.com/JeffLIrion/adb_shell                              |
| aiofiles                   | 25.1.0    | Apache Software License              | https://github.com/Tinche/aiofiles                                   |
| aiohappyeyeballs           | 2.7.1     | Python Software Foundation License   | https://github.com/aio-libs/aiohappyeyeballs                         |
| aiohttp                    | 3.14.1    | Apache-2.0 AND MIT                   | https://github.com/aio-libs/aiohttp                                  |
| aiosignal                  | 1.4.0     | Apache Software License              | https://github.com/aio-libs/aiosignal                                |
| aiowebostv                 | 0.7.5     | Apache-2.0                           | UNKNOWN                                                              |
| androidtvremote2           | 0.3.1     | Apache-2.0                           | https://github.com/tronikos/androidtvremote2                         |
| annotated-types            | 0.7.0     | MIT License                          | https://github.com/annotated-types/annotated-types                   |
| async-timeout              | 5.0.1     | Apache Software License              | https://github.com/aio-libs/async-timeout                            |
| async_upnp_client          | 0.47.0    | Apache-2.0                           | UNKNOWN                                                              |
| attrs                      | 26.1.0    | MIT                                  | https://www.attrs.org/en/stable/changelog.html                       |
| awesomeversion             | 25.8.0    | MIT                                  | https://github.com/ludeeus/awesomeversion                            |
| backoff                    | 2.2.1     | MIT License                          | https://github.com/litl/backoff                                      |
| certifi                    | 2026.6.17 | Mozilla Public License 2.0 (MPL 2.0) | https://github.com/certifi/python-certifi                            |
| cffi                       | 2.1.0     | MIT-0                                | https://cffi.readthedocs.io/en/latest/whatsnew.html                  |
| chacha20poly1305-reuseable | 0.13.2    | Other/Proprietary License            | https://github.com/bdraco/chacha20poly1305-reuseable                 |
| charset-normalizer         | 3.4.9     | MIT                                  | https://github.com/jawah/charset_normalizer/blob/master/CHANGELOG.md |
| cryptography               | 49.0.0    | Apache-2.0 OR BSD-3-Clause           | https://github.com/pyca/cryptography                                 |
| defusedxml                 | 0.7.1     | Python Software Foundation License   | https://github.com/tiran/defusedxml                                  |
| frozenlist                 | 1.8.0     | Apache-2.0                           | https://github.com/aio-libs/frozenlist                               |
| idna                       | 3.18      | BSD-3-Clause                         | https://github.com/kjd/idna                                          |
| ifaddr                     | 0.2.0     | MIT License                          | https://github.com/pydron/ifaddr                                     |
| linkify-it-py              | 2.1.0     | MIT License                          | https://github.com/tsutsu3/linkify-it-py                             |
| markdown-it-py             | 4.2.0     | MIT License                          | https://github.com/executablebooks/markdown-it-py                    |
| mdit-py-plugins            | 0.6.1     | MIT License                          | https://github.com/executablebooks/mdit-py-plugins                   |
| mdurl                      | 0.1.2     | MIT License                          | https://github.com/executablebooks/mdurl                             |
| miniaudio                  | 1.71      | MIT License                          | https://github.com/irmen/pyminiaudio                                 |
| multidict                  | 6.7.1     | Apache License 2.0                   | https://github.com/aio-libs/multidict                                |
| platformdirs               | 4.10.0    | MIT                                  | https://github.com/tox-dev/platformdirs                              |
| propcache                  | 0.5.2     | Apache Software License              | https://github.com/aio-libs/propcache                                |
| protobuf                   | 7.35.1    | 3-Clause BSD License                 | https://developers.google.com/protocol-buffers/                      |
| pyasn1                     | 0.6.4     | BSD-2-Clause                         | https://github.com/pyasn1/pyasn1                                     |
| pyatv                      | 0.18.0    | MIT                                  | https://pyatv.dev                                                    |
| pycparser                  | 3.0       | BSD-3-Clause                         | https://github.com/eliben/pycparser                                  |
| pydantic                   | 2.13.4    | MIT                                  | https://github.com/pydantic/pydantic                                 |
| pydantic_core              | 2.46.4    | MIT                                  | https://github.com/pydantic                                          |
| python-didl-lite           | 1.5.0     | Apache-2.0                           | UNKNOWN                                                              |
| requests                   | 2.34.2    | Apache Software License              | https://github.com/psf/requests                                      |
| rich                       | 14.3.4    | MIT License                          | https://github.com/Textualize/rich                                   |
| rokuecp                    | 0.19.5    | MIT License                          | https://github.com/ctalkington/python-rokuecp                        |
| rsa                        | 4.9.1     | Apache Software License              | https://stuvel.eu/rsa                                                |
| samsungtvws                | 3.0.5     | LGPL-3.0                             | UNKNOWN                                                              |
| six                        | 1.17.0    | MIT License                          | https://github.com/benjaminp/six                                     |
| srptools                   | 1.0.1     | BSD License                          | https://github.com/idlesign/srptools                                 |
| tabulate                   | 0.10.0    | MIT                                  | https://github.com/astanin/python-tabulate                           |
| textual                    | 8.2.8     | MIT License                          | https://github.com/Textualize/textual                                |
| tinytag                    | 2.2.1     | MIT License                          | https://github.com/tinytag/tinytag                                   |
| typing-inspection          | 0.4.2     | MIT                                  | https://github.com/pydantic/typing-inspection                        |
| typing_extensions          | 4.16.0    | PSF-2.0                              | https://github.com/python/typing_extensions                          |
| uc-micro-py                | 2.0.0     | MIT License                          | https://github.com/tsutsu3/uc.micro-py                               |
| urllib3                    | 2.7.0     | MIT                                  | https://github.com/urllib3/urllib3/blob/main/CHANGES.rst             |
| voluptuous                 | 0.16.0    | BSD License                          | https://github.com/alecthomas/voluptuous                             |
| websocket-client           | 1.9.0     | Apache Software License              | https://github.com/websocket-client/websocket-client.git             |
| websockets                 | 16.0      | BSD-3-Clause                         | https://github.com/python-websockets/websockets                      |
| xmltodict                  | 1.0.4     | MIT                                  | https://github.com/martinblech/xmltodict                             |
| yarl                       | 1.24.2    | Apache-2.0                           | https://github.com/aio-libs/yarl                                     |
| zeroconf                   | 0.150.0   | LGPL-2.1-or-later                    | https://github.com/python-zeroconf/python-zeroconf                   |

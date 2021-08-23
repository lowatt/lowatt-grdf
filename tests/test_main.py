# The MIT License
#
# Copyright (c) 2021 Lowatt <info@lowatt.fr>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from click.testing import CliRunner

from lowatt_grdf import main


def test_cli_base() -> None:
    runner = CliRunner()
    result = runner.invoke(main.main)
    assert result.exit_code == 0
    assert (
        result.stdout
        == """Usage: main [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  declare-acces
  donnees-consos-informatives
  donnees-consos-publiees
  donnees-contractuelles
  donnees-techniques
  droits-acces
"""
    )


def test_cli_declare_acces() -> None:
    runner = CliRunner()
    result = runner.invoke(main.main, ["declare-acces", "--help"])
    assert result.exit_code == 0
    assert (
        result.stdout
        == """Usage: main declare-acces [OPTIONS]

Options:
  --bas                           Use staging (bac à sable) environment
  --client-secret TEXT            openid client id  [required]
  --client-id TEXT                openid client id  [required]
  --pce TEXT                      [required]
  --role-tiers TEXT
  --raison-sociale TEXT
  --nom-titulaire TEXT
  --code-postal TEXT              [required]
  --courriel-titulaire TEXT       [required]
  --date-consentement-declaree TEXT
                                  [required]
  --date-fin-autorisation-demandee TEXT
                                  [required]
  --perim-donnees-techniques-et-contractuelles
  --perim-historique-de-donnees
  --perim-flux-de-donnees
  --perim-donnees-informatives
  --perim-donnees-publiees
  --help                          Show this message and exit.
"""
    )

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

import logging
import os
import sys
from typing import Any, Callable, Union

import attrs
import click
import requests
import rich

from . import LOGGER, api, models

Callback = Callable[..., None]


def api_options(func: Callback) -> Callback:
    click.option(
        "--client-id",
        required="CLIENT_ID" not in os.environ,
        default=os.environ.get("CLIENT_ID"),
        help="openid client id",
    )(func)
    click.option(
        "--client-secret",
        required="CLIENT_SECRET" not in os.environ,
        default=os.environ.get("CLIENT_SECRET"),
        help="openid client secret",
    )(func)
    click.option(
        "--bas",
        default=False,
        is_flag=True,
        help="Use staging (bac à sable) environment",
    )(func)
    return func


def options_from_model(
    model: Any,
) -> Callable[[Callback], Callback]:
    def decorator(func: Callback) -> Callback:
        for field in reversed(attrs.fields(model)):
            opt = field.alias.replace("_", "-")
            opt = f"--{opt}"
            kwargs: dict[str, Union[str, bool]] = {}
            if field.default == attrs.NOTHING:
                kwargs["required"] = True
            else:
                kwargs.update(required=False, default=field.default)
            if field.type == bool:
                kwargs["is_flag"] = True
            if field.alias.startswith("date_"):
                kwargs["metavar"] = "YYYY-MM-DD"
            click.option(opt, **kwargs)(func)  # type: ignore[arg-type]
        return func

    return decorator


class ExceptionHandler(click.Group):
    def __call__(self, *args: Any, **kwargs: Any) -> None:
        try:
            self.main(*args, **kwargs)
        except requests.HTTPError as exc:
            LOGGER.error(exc)
            sys.exit(1)


@click.group(
    cls=ExceptionHandler, context_settings={"help_option_names": ["-h", "--help"]}
)
def main() -> None:
    logging.basicConfig(level="INFO", format="%(levelname)s %(message)s")


@main.command()
@click.argument("pce", nargs=-1)
@click.option(
    "--check",
    default=False,
    is_flag=True,
    help="Check droits-access and exit with error in case of consent validation error",
)
@api_options
def droits_acces(
    client_id: str, client_secret: str, bas: bool, pce: tuple[str], check: bool
) -> None:
    grdf = {True: api.StagingAPI, False: api.API}[bas](client_id, client_secret)
    if check:
        grdf.check_consent_validation(list(pce))
    else:
        rich.print_json(data=grdf.droits_acces(list(pce)))


@main.command()
@click.argument("pce", nargs=-1)
@click.option(
    "--role", type=click.Choice(api.BaseAPI.DEFAULT_THIRD_ROLE), multiple=True
)
@click.option(
    "--etat", type=click.Choice(api.BaseAPI.DEFAULT_ACCESS_RIGHT_STATE), multiple=True
)
@click.option(
    "--preuve",
    type=click.Choice(api.BaseAPI.DEFAULT_PROOF_CONTROL_STATUS),
    multiple=True,
)
@api_options
def droits_acces_specifiques(
    client_id: str,
    client_secret: str,
    bas: bool,
    pce: tuple[str],
    role: tuple[api.BaseAPI.ThirdRole],
    etat: tuple[api.BaseAPI.AccessRightState],
    preuve: tuple[api.BaseAPI.ProofControlStatus],
) -> None:
    grdf = {True: api.StagingAPI, False: api.API}[bas](client_id, client_secret)
    rich.print_json(
        data=grdf.droits_acces_specifiques(
            list(pce),
            third_role=role,
            access_right_state=etat,
            proof_control_status=preuve,
        )
    )


@main.command()
@click.argument("pce")
@click.option("--from-date", required=True)
@click.option("--to-date", required=True)
@api_options
def donnees_consos_publiees(
    client_id: str,
    client_secret: str,
    bas: bool,
    pce: str,
    from_date: str,
    to_date: str,
) -> None:
    grdf = {True: api.StagingAPI, False: api.API}[bas](client_id, client_secret)
    rich.print_json(data=grdf.donnees_consos_publiees(pce, from_date, to_date))


@main.command()
@click.argument("pce")
@click.option("--from-date", required=True)
@click.option("--to-date", required=True)
@api_options
def donnees_consos_informatives(
    client_id: str,
    client_secret: str,
    bas: bool,
    pce: str,
    from_date: str,
    to_date: str,
) -> None:
    grdf = {True: api.StagingAPI, False: api.API}[bas](client_id, client_secret)
    rich.print_json(data=grdf.donnees_consos_informatives(pce, from_date, to_date))


@main.command()
@click.argument("pce")
@api_options
def donnees_contractuelles(
    client_id: str,
    client_secret: str,
    bas: bool,
    pce: str,
) -> None:
    grdf = {True: api.StagingAPI, False: api.API}[bas](client_id, client_secret)
    rich.print_json(data=grdf.donnees_contractuelles(pce))


@main.command()
@click.argument("pce")
@api_options
def donnees_techniques(
    client_id: str,
    client_secret: str,
    bas: bool,
    pce: str,
) -> None:
    grdf = {True: api.StagingAPI, False: api.API}[bas](client_id, client_secret)
    rich.print_json(data=grdf.donnees_techniques(pce))


@main.command()
@api_options
@options_from_model(models.DeclareAccess)
def declare_acces(
    client_id: str,
    client_secret: str,
    bas: bool,
    **kwargs: Any,
) -> None:
    access = models.DeclareAccess(**kwargs)
    grdf = {True: api.StagingAPI, False: api.API}[bas](client_id, client_secret)
    grdf.declare_acces(access)

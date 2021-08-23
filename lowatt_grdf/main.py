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

import json
import logging
import os
import sys
from typing import Any, Callable, Tuple, Type

import click
import pydantic

from . import api, models

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
        help="openid client id",
    )(func)
    click.option(
        "--bas",
        default=False,
        is_flag=True,
        help="Use staging (bac à sable) environment",
    )(func)
    return func


def options_from_model(
    model: Type[pydantic.BaseModel],
) -> Callable[[Callback], Callback]:
    def decorator(func: Callback) -> Callback:
        for field in reversed(list(model.__fields__.values())):
            opt = field.alias.replace("_", "-")
            opt = f"--{opt}"
            kwargs = {
                "required": field.required,
                "default": field.default,
            }
            if field.field_info.description is not None:
                kwargs["help"] = field.field_info.description
            if field.type_ == bool:
                kwargs["is_flag"] = True
            click.option(opt, **kwargs)(func)
        return func

    return decorator


@click.group()
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
    client_id: str, client_secret: str, bas: bool, pce: Tuple[str], check: bool
) -> None:
    grdf = {True: api.StagingAPI, False: api.API}[bas](client_id, client_secret)
    if check:
        grdf.check_consent_validation(list(pce))
    else:
        json.dump(grdf.droits_acces(list(pce)), sys.stdout)


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
    json.dump(grdf.donnees_consos_publiees(pce, from_date, to_date), sys.stdout)


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
    json.dump(grdf.donnees_consos_informatives(pce, from_date, to_date), sys.stdout)


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
    json.dump(grdf.donnees_contractuelles(pce), sys.stdout)


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
    json.dump(grdf.donnees_techniques(pce), sys.stdout)


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

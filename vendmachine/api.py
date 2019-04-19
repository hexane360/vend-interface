#!/usr/bin/env python3

from flask import Blueprint, request, abort

from vendmachine.server import app
from vendmachine.settings import settings

api = Blueprint("api", __name__)

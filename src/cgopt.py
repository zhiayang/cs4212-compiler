#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

__opts_enabled = False

def optimising() -> bool:
	global __opts_enabled
	return __opts_enabled

def enable_optimisations(en: bool = True):
	global __opts_enabled
	__opts_enabled = en

def disable_optimisations():
	global __opts_enabled
	__opts_enabled = False


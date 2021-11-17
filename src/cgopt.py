#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

__opts_enabled = False
__annotations_enabled = True

def optimising() -> bool:
	global __opts_enabled
	return __opts_enabled

def enable_optimisations(en: bool = True):
	global __opts_enabled
	__opts_enabled = en

def disable_optimisations():
	global __opts_enabled
	__opts_enabled = False



def annotating() -> bool:
	global __annotations_enabled
	return __annotations_enabled

def enable_annotations(en: bool = True):
	global __opts_enabled
	__opts_enabled = en

def disable_annotations():
	global __opts_enabled
	__opts_enabled = False

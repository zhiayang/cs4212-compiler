#/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

__opts_enabled = False
__annotations_enabled = True
__is_verbose = False
__print_lowered_ir = False
__print_opt_ir = False
__print_ir = False


def should_print_lowered_ir():
	global __print_lowered_ir
	return __print_lowered_ir

def enable_print_lowered_ir(en: bool = True):
	global __print_lowered_ir
	__print_lowered_ir = en


def should_print_ir():
	global __print_ir
	return __print_ir

def enable_print_ir(en: bool = True):
	global __print_ir
	__print_ir = en


def should_print_optimised_ir():
	global __print_opt_ir
	return __print_opt_ir

def enable_print_optimised_ir(en: bool = True):
	global __print_opt_ir
	__print_opt_ir = en




def is_verbose() -> bool:
	global __is_verbose
	return __is_verbose

def enable_verbose(en: bool = True):
	global __is_verbose
	__is_verbose = en

def disable_verbose():
	global __is_verbose
	__is_verbose = False


def annotations_enabled() -> bool:
	global __annotations_enabled
	return __annotations_enabled

def enable_annotations(en: bool = True):
	global __annotations_enabled
	__annotations_enabled = en

def disable_annotations():
	global __annotations_enabled
	__annotations_enabled = False


def optimisations_enabled() -> bool:
	global __opts_enabled
	return __opts_enabled

def enable_optimisations(en: bool = True):
	global __opts_enabled
	__opts_enabled = en

def disable_optimisations():
	global __opts_enabled
	__opts_enabled = False


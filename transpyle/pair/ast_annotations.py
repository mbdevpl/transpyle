
import logging
import typing as t

import typed_ast.ast3 as typed_ast3

_LOG = logging.getLogger(__name__)

AST_ANNOTATION_FIELD = 'annotations'


def annotate_ast(node: typed_ast3.AST, key: str, value: t.Any):
    annotations = getattr(node, AST_ANNOTATION_FIELD, None)
    if annotations is None:
        annotations = {}
        setattr(node, AST_ANNOTATION_FIELD, annotations)
    if key in annotations:
        _LOG.warning('node %s already has an annotation %s', type(node).__name__, key)
    annotations[key] = value


def has_annotations(node: typed_ast3.AST):
    return len(getattr(node, AST_ANNOTATION_FIELD, {})) > 0


def has_annotation(node: typed_ast3.AST, key: str):
    return has_annotations(node) and key in getattr(node, AST_ANNOTATION_FIELD)


def get_annotation(node: typed_ast3.AST, key: str) -> t.Any:
    if not has_annotation(node, key):
        return None
    return getattr(node, AST_ANNOTATION_FIELD)[key]

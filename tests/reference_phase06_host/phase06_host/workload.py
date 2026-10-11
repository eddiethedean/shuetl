"""Canonical specification used by installed CLI qualification."""

from etlantic import Data, Extract, Load, Pipeline
from etlantic.authoring import definition_from_pipeline
from etlantic.authoring.serialize import pipeline_to_dict


class Row(Data):
    id: str
    payload: str


class Transfer(Pipeline):
    source: Extract[Row] = Extract(asset="source")
    sink: Load[Row] = Load(input=source.result, asset="sink")


def specification():
    return pipeline_to_dict(definition_from_pipeline(Transfer))

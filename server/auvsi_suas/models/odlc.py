"""Object detection, localization, and classification model."""

import enum
import logging
import networkx as nx
import operator
from auvsi_suas.models import pb_utils
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.proto import interop_admin_api_pb2
from auvsi_suas.proto import interop_api_pb2
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)

# Ratio of object points to lose for every extra unmatched object submitted.
EXTRA_OBJECT_PENALTY_RATIO = 0.05
# The weight of classification accuracy when calculating a odlc match score.
CHARACTERISTICS_WEIGHT = 0.4
# The lowest allowed location accuracy (in feet)
TARGET_LOCATION_THRESHOLD = 150
# The weight of geolocation accuracy when calculating a odlc match score.
GEOLOCATION_WEIGHT = 0.4
# The weight of actionable intelligence when calculating a odlc match score.
ACTIONABLE_WEIGHT = 0.1
# The weight of autonomy when calculating a odlc match score.
AUTONOMY_WEIGHT = 0.1


class Odlc(models.Model):
    """Object detection submission for a team."""

    # The mission this is an ODLC for.
    mission = models.ForeignKey('MissionConfig', on_delete=models.CASCADE)
    # The user which submitted and owns this object detection.
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             db_index=True,
                             on_delete=models.CASCADE)
    # Object type.
    odlc_type = models.IntegerField(
        choices=pb_utils.FieldChoicesFromEnum(interop_api_pb2.Odlc.Type))
    # Object location.
    location = models.ForeignKey(GpsPosition,
                                 null=True,
                                 blank=True,
                                 on_delete=models.CASCADE)
    # Object orientation.
    orientation = models.IntegerField(choices=pb_utils.FieldChoicesFromEnum(
        interop_api_pb2.Odlc.Orientation),
                                      null=True,
                                      blank=True)
    # Object shape.
    shape = models.IntegerField(choices=pb_utils.FieldChoicesFromEnum(
        interop_api_pb2.Odlc.Shape),
                                null=True,
                                blank=True)
    # Object background color.
    shape_color = models.IntegerField(choices=pb_utils.FieldChoicesFromEnum(
        interop_api_pb2.Odlc.Color),
                                      null=True,
                                      blank=True)
    # Object alphanumeric.
    alphanumeric = models.TextField(default='', blank=True)
    # Object alphanumeric color.
    alphanumeric_color = models.IntegerField(
        choices=pb_utils.FieldChoicesFromEnum(interop_api_pb2.Odlc.Color),
        null=True,
        blank=True)
    # Free-form object description.
    description = models.TextField(default='', blank=True)
    # Whether judge considers description valid.
    description_approved = models.NullBooleanField()
    # Object is an ADLC submission.
    autonomous = models.BooleanField(default=False)
    # Uploaded object image thumbnail.
    thumbnail = models.ImageField(upload_to='objects', blank=True)
    # Whether judge considers thumbnail valid for object.
    thumbnail_approved = models.NullBooleanField()
    # Time that this object was first created.
    creation_time = models.DateTimeField()
    # Time that this object was last modified.
    last_modified_time = models.DateTimeField()

    def __init__(self, *args, **kwargs):
        super(Odlc, self).__init__(*args, **kwargs)
        if not self.creation_time or not self.last_modified_time:
            self.update_last_modified()

    def update_last_modified(self):
        """Updates timestamps for modification."""
        self.last_modified_time = timezone.now()
        if not self.creation_time:
            self.creation_time = self.last_modified_time

    def similar_orientation(self, other):
        """Compares the orientations for equality.

        Some alphanumerics can have multiple allowed orientations.

        Args:
            other: Another object for which to compare.
        Returns:
            True if the orientations can be considered equal.
        """
        if self.orientation == other.orientation:
            return True

        accepts_any = ['o', 'O', '0']
        if self.alphanumeric in accepts_any:
            return True

        accepts_rotation = [
            'H', 'I', 'N', 'o', 'O', 's', 'S', 'x', 'X', 'z', 'Z', '0', '8'
        ]
        rotated = {
            interop_api_pb2.Odlc.N: interop_api_pb2.Odlc.S,
            interop_api_pb2.Odlc.NE: interop_api_pb2.Odlc.SW,
            interop_api_pb2.Odlc.E: interop_api_pb2.Odlc.W,
            interop_api_pb2.Odlc.SE: interop_api_pb2.Odlc.NW,
            interop_api_pb2.Odlc.S: interop_api_pb2.Odlc.N,
            interop_api_pb2.Odlc.SW: interop_api_pb2.Odlc.NE,
            interop_api_pb2.Odlc.W: interop_api_pb2.Odlc.E,
            interop_api_pb2.Odlc.NW: interop_api_pb2.Odlc.SE,
        }
        if (self.alphanumeric in accepts_rotation
                and rotated[self.orientation] == other.orientation):
            return True

        return False

    def similar_classifications_ratio(self, other):
        """Counts the number of similar classification attributes.

        Args:
            other: Another object for which to compare.
        Returns:
            The ratio of attributes which are the same.
        """
        # Cannot have similar fields with different type objects.
        if self.odlc_type != other.odlc_type:
            return 0

        # Emergent only compares descriptions.
        if self.odlc_type == interop_api_pb2.Odlc.EMERGENT:
            if self.description_approved == other.description_approved:
                return 1
            return 0

        # Compare the fields which require equality.
        direct_compare_fields = [
            'shape', 'shape_color', 'alphanumeric', 'alphanumeric_color'
        ]
        similar_fields = 0
        total_fields = len(direct_compare_fields)
        for field in direct_compare_fields:
            if getattr(self, field) == getattr(other, field):
                similar_fields += 1

        # Compare orientation, accounting for multiple acceptable orientations.
        total_fields += 1
        if self.similar_orientation(other):
            similar_fields += 1

        return float(similar_fields) / total_fields

    def actionable_submission(self, flights):
        """Checks if Odlc meets Actionable Intelligence submission criteria."""
        actionable = False
        if len(flights) > 0:
            flight = flights[0]
            if flight.within(self.creation_time) and \
                flight.within(self.last_modified_time):
                actionable = True
        return actionable


class OdlcEvaluator(object):
    """Evaluates submitted objects against real judge-made objects."""
    def __init__(self, submitted_objects, real_objects, flights):
        """Creates an evaluation of submitted objects against real objects.

        Args:
            submitted_objects: List of submitted Odlc objects, all from
                               the same user.
            real_objects: List of real objects made by judges.
            flights: Flights for the ODLC's user.

        Raises:
            AssertionError: not all submitted objects are from the same user.
        """
        self.submitted_objects = submitted_objects
        self.real_objects = real_objects
        self.flights = flights

        if self.submitted_objects:
            self.user = self.submitted_objects[0].user
            for t in self.submitted_objects:
                if t.user != self.user:
                    raise AssertionError(
                        "All submitted objects must be from the same user")

        self.matches = self.match_odlcs(submitted_objects, real_objects)
        self.unmatched = self.find_unmatched(submitted_objects, real_objects,
                                             self.matches)

    def range_lookup(self,
                     ranges,
                     key,
                     start_operator=operator.ge,
                     end_operator=operator.le):
        """Performs a range based lookup.

        Args:
            ranges: A list of maps containing start,end,value keys.
            key: The key for the range lookup.
            start_operator: The operator to compare the start key against.
            end_operator: The operator to compare the end key against.
        Returns:
            The value associated for the range lookup, or None if not in range.
        """
        for r in ranges:
            if start_operator(key, r['start']) and end_operator(key, r['end']):
                return r['value']
        return None

    def evaluate_match(self, submitted, real):
        """Evaluates the match if the two objects were to be paired.

        Args:
            submitted: The team submitted object. Must be one of
                self.submitted_objects.
            real: The real object made by the judges. Must be one of
                self.real_objects.
        Returns:
            auvsi_suas.proto.OdlcEvaluation. The match evaluation.
        """
        object_eval = interop_admin_api_pb2.OdlcEvaluation()
        object_eval.real_odlc = real.pk
        object_eval.submitted_odlc = submitted.pk
        object_eval.score_ratio = 0

        # Odlcs which are not the same type have no match value.
        if submitted.odlc_type != real.odlc_type:
            return object_eval
        # Odlcs which don't have an approved thumbnail have no value.
        if not submitted.thumbnail_approved:
            return object_eval

        # Compute values which influence score and are provided as feedback.
        if submitted.thumbnail_approved is not None:
            object_eval.image_approved = submitted.thumbnail_approved
        if (submitted.odlc_type == interop_api_pb2.Odlc.EMERGENT
                and submitted.description_approved is not None):
            object_eval.description_approved = submitted.description_approved
        object_eval.classifications_ratio = real.similar_classifications_ratio(
            submitted)
        if submitted.location:
            object_eval.geolocation_accuracy_ft = \
                    submitted.location.distance_to(real.location)
        object_eval.actionable_submission = submitted.actionable_submission(
            flights=self.flights)
        object_eval.autonomous_submission = submitted.autonomous

        # Compute score.
        object_eval.classifications_score_ratio = \
                object_eval.classifications_ratio
        if object_eval.HasField('geolocation_accuracy_ft'):
            object_eval.geolocation_score_ratio = max(
                0, (float(TARGET_LOCATION_THRESHOLD) -
                    object_eval.geolocation_accuracy_ft) /
                float(TARGET_LOCATION_THRESHOLD))
        else:
            object_eval.geolocation_score_ratio = 0
        object_eval.actionable_score_ratio = \
                1 if object_eval.actionable_submission else 0
        object_eval.autonomous_score_ratio = \
                1 if object_eval.autonomous_submission else 0
        object_eval.score_ratio = (
            (CHARACTERISTICS_WEIGHT * object_eval.classifications_score_ratio)
            + (GEOLOCATION_WEIGHT * object_eval.geolocation_score_ratio) +
            (ACTIONABLE_WEIGHT * object_eval.actionable_score_ratio) +
            (AUTONOMY_WEIGHT * object_eval.autonomous_score_ratio))

        return object_eval

    def matching_map_from_set(self, matched_set):
        """Converts mapping set-of-pairs format to a map format."""
        matches = {}
        for (f, s) in matched_set:
            matches[f] = s
            matches[s] = f
        return matches

    def match_odlcs(self, submitted_objects, real_objects):
        """Matches the objects to maximize match value.

        Args:
            submitted_objects: List of submitted object detections.
            real_objects: List of real objects made by judges.
        Returns:
            A map from submitted object to real object, and real object to
            submitted object, if they are matched.
        """
        # Create a bipartite graph from submitted to real objects with match
        # values (score ratio) as edge weights. Skip edges with no match value.
        g = nx.Graph()
        g.add_nodes_from(submitted_objects)
        g.add_nodes_from(real_objects)
        for submitted in submitted_objects:
            for real in real_objects:
                match_value = self.evaluate_match(submitted, real).score_ratio
                if match_value:
                    g.add_edge(submitted, real, weight=match_value)
        # Compute the full matching.
        return self.matching_map_from_set(
            nx.algorithms.matching.max_weight_matching(g))

    def find_unmatched(self, submitted_objects, real_objects, matches):
        """Finds unmatched objects, filtering double-counts by autonomy.

        Args:
            submitted_objects: List of submitted object detections.
            real_objects: List of real objects made by judges.
            matches: Map from submitted to real objects indicating matches.
        Returns:
            List of objects which are unmatched after filtering autonomy
            duplicates.
        """
        # Create a bipartite graph from unsubmitted to real objects with match
        # values (score ratio) as edge weights. Skip edges with no match value.
        # Skip edges if not inverse autonomy for existing match.
        remaining_objects = [t for t in submitted_objects if t not in matches]
        g = nx.Graph()
        g.add_nodes_from(remaining_objects)
        g.add_nodes_from(real_objects)
        for submitted in remaining_objects:
            for real in real_objects:
                match_value = self.evaluate_match(submitted, real).score_ratio
                inverted_autonomy = (
                    real in matches
                    and submitted.autonomous != matches[real].autonomous)
                if match_value and inverted_autonomy:
                    # We care about minimizing unmatched, not match weight, so
                    # use weight of 1.
                    g.add_edge(submitted, real, weight=1)
        # Compute the matching to find unused objects.
        unused_match = self.matching_map_from_set(
            nx.algorithms.matching.max_weight_matching(g))
        # Difference between remaining and unused is unmatched.
        return [t for t in remaining_objects if t not in unused_match]

    def evaluate(self):
        """Evaluates the submitted objects.

        Returns:
            auvsi_suas.proto.MultiOdlcEvaluation.
        """
        multi_eval = interop_admin_api_pb2.MultiOdlcEvaluation()
        # Compute match value.
        for real in self.real_objects:
            object_eval = multi_eval.odlcs.add()
            object_eval.real_odlc = real.pk
            object_eval.score_ratio = 0
            submitted = self.matches.get(real)
            if submitted:
                object_eval.CopyFrom(self.evaluate_match(submitted, real))
        if self.real_objects:
            multi_eval.matched_score_ratio = sum(
                [e.score_ratio
                 for e in multi_eval.odlcs]) / len(self.real_objects)
        else:
            multi_eval.matched_score_ratio = 0
        # Compute extra object penalty.
        multi_eval.unmatched_odlc_count = len(self.unmatched)
        multi_eval.extra_object_penalty_ratio = \
                (multi_eval.unmatched_odlc_count *
                        EXTRA_OBJECT_PENALTY_RATIO)
        # Compute total score.
        multi_eval.score_ratio = (multi_eval.matched_score_ratio -
                                  multi_eval.extra_object_penalty_ratio)
        return multi_eval


@admin.register(Odlc)
class OdlcModelAdmin(admin.ModelAdmin):
    show_full_result_count = False
    raw_id_fields = ("location", )
    list_display = ('pk', 'user', 'odlc_type', 'shape_color', 'shape',
                    'alphanumeric_color', 'alphanumeric', 'location',
                    'orientation', 'autonomous', 'thumbnail_approved',
                    'creation_time', 'last_modified_time')

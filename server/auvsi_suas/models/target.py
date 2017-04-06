"""Target model."""

import collections
import enum
import networkx as nx
import operator
from auvsi_suas.proto import target_pb2
from django.conf import settings
from django.db import models
from gps_position import GpsPosition
from takeoff_or_landing_event import TakeoffOrLandingEvent
from mission_clock_event import MissionClockEvent


class Choices(enum.IntEnum):
    """Base class for enums used to limit Django field choices,
    plus other helper methods.

    Item names should be lowercase to work properly with lookup().
    """

    @classmethod
    def choices(cls):
        """Provide choices for Django's IntField.choices.

        Returns:
            Enum values in an iterator to be passed to IntField.choices.
            The enum value is used as the field key, and the name as the
            description.
        """
        return [(int(v), k) for k, v in cls.__members__.items()]

    @classmethod
    def lookup(cls, s):
        """Lookup value from name.

        Args:
            s: name to lookup; case insensitive

        Returns:
            Value associated with name

        Raises:
            KeyError: name not valid
        """
        return cls.__members__[str(s).lower()]

    @classmethod
    def names(cls):
        """Names of choices

        Returns:
            List of names of values
        """
        return cls.__members__.keys()


@enum.unique
class TargetType(Choices):
    """Valid target types.

    Warning: DO NOT change/reuse values, or compatibility will be lost with
    old data sets. Only add new values to the end. Next value is 5.
    """
    standard = 1
    off_axis = 3
    emergent = 4


@enum.unique
class Orientation(Choices):
    """Valid target orientations.

    Warning: DO NOT change/reuse values, or compatibility will be lost with
    old data sets. Only add new values to the end.
    """
    n = 1
    ne = 2
    e = 3
    se = 4
    s = 5
    sw = 6
    w = 7
    nw = 8


@enum.unique
class Shape(Choices):
    """Valid target shapes.

    Warning: DO NOT change/reuse values, or compatibility will be lost with
    old data sets. Only add new values to the end. Next value is 14.
    """
    circle = 1
    semicircle = 2
    quarter_circle = 3
    triangle = 4
    square = 5
    rectangle = 6
    trapezoid = 7
    pentagon = 8
    hexagon = 9
    heptagon = 10
    octagon = 11
    star = 12
    cross = 13


@enum.unique
class Color(Choices):
    """Valid target colors.

    Warning: DO NOT change/reuse values, or compatibility will be lost with
    old data sets. Only add new values to the end. Next value is 11.
    """
    white = 1
    black = 2
    gray = 3
    red = 4
    blue = 5
    green = 6
    yellow = 7
    purple = 8
    brown = 9
    orange = 10


class Target(models.Model):
    """Target represents a single target submission for a team.

    Attributes:
        user: The user which submitted and owns this target.
        target_type: Target type.
        location: Target location.
        orientation: Target orientation.
        shape: Target shape.
        background_color: Target background color.
        alphanumeric: Target alphanumeric.
        alphanumeric_color: Target alphanumeric color.
        description: Free-form target description.
        description_approved: Whether judge considers description valid.
        autonomous: Target is an ADLC submission.
        thumbnail: Uploaded target image thumbnail.
        thumbnail_approved: Whether judge considers thumbnail valid for target.
        creation_time: Time that this target was first created.
        last_modified_time: Time that this target was last modified.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True)
    target_type = models.IntegerField(choices=TargetType.choices())
    location = models.ForeignKey(GpsPosition, null=True, blank=True)
    orientation = models.IntegerField(choices=Orientation.choices(),
                                      null=True,
                                      blank=True)
    shape = models.IntegerField(choices=Shape.choices(), null=True, blank=True)
    background_color = models.IntegerField(choices=Color.choices(),
                                           null=True,
                                           blank=True)
    alphanumeric = models.TextField(default='', blank=True)
    alphanumeric_color = models.IntegerField(choices=Color.choices(),
                                             null=True,
                                             blank=True)
    description = models.TextField(default='', blank=True)
    description_approved = models.NullBooleanField()
    autonomous = models.BooleanField(default=False)
    thumbnail = models.ImageField(upload_to='targets', blank=True)
    thumbnail_approved = models.NullBooleanField()
    creation_time = models.DateTimeField(auto_now_add=True)
    last_modified_time = models.DateTimeField(auto_now=True)
    actionable_override = models.BooleanField(default=False)

    def __unicode__(self):
        """Descriptive text for use in displays."""
        d = self.json(is_superuser=True)
        return unicode('{name}({fields})'.format(
            name=self.__class__.__name__,
            fields=', '.join('%s=%s' % (k, v) for k, v in d.iteritems())))

    def json(self, is_superuser=False):
        """Target as dict, for JSON."""
        target_type = None
        if self.target_type is not None:
            target_type = TargetType(self.target_type).name

        latitude = None
        longitude = None
        if self.location is not None:
            latitude = self.location.latitude
            longitude = self.location.longitude

        orientation = None
        if self.orientation is not None:
            orientation = Orientation(self.orientation).name

        shape = None
        if self.shape is not None:
            shape = Shape(self.shape).name

        background_color = None
        if self.background_color is not None:
            background_color = Color(self.background_color).name

        alphanumeric = None
        if self.alphanumeric != '':
            alphanumeric = self.alphanumeric

        alphanumeric_color = None
        if self.alphanumeric_color is not None:
            alphanumeric_color = Color(self.alphanumeric_color).name

        description = None
        if self.description != '':
            description = self.description

        d = {
            'id': self.pk,
            'user': self.user.pk,
            'type': target_type,
            'latitude': latitude,
            'longitude': longitude,
            'orientation': orientation,
            'shape': shape,
            'background_color': background_color,
            'alphanumeric': alphanumeric,
            'alphanumeric_color': alphanumeric_color,
            'description': description,
            'autonomous': self.autonomous,
        }

        if is_superuser:
            d['description_approved'] = self.description_approved
            d['thumbnail'] = self.thumbnail.name if self.thumbnail else None
            d['thumbnail_approved'] = self.thumbnail_approved
            d['creation_time'] = self.creation_time
            d['last_modified_time'] = self.last_modified_time
            d['actionable_override'] = self.actionable_override

        return d

    def similar_classifications_ratio(self, other):
        """Counts the number of similar classification attributes.

        Args:
            other: Another target for which to compare.
        Returns:
            The ratio of attributes which are the same.
        """
        # Cannot have similar fields with different type targets.
        if self.target_type != other.target_type:
            return 0

        standard_fields = ['orientation', 'shape', 'background_color',
                           'alphanumeric', 'alphanumeric_color']
        classify_fields = {
            TargetType.standard: standard_fields,
            TargetType.off_axis: standard_fields,
            TargetType.emergent: ['description_approved'],
        }
        fields = classify_fields[self.target_type]
        count = 0
        for field in fields:
            if getattr(self, field) == getattr(other, field):
                count += 1
        return float(count) / len(fields)

    def actionable_submission(self, flights=None):
        """Checks if Target meets Actionable Intelligence submission criteria.

        A target is "actionable" if one of the following conditions is met:
            (a) If it was submitted over interop and last updated during the
                aircraft's first flight.
            (b) If the target was submitted via USB, the target's
                actionable_override flag was set by an admin.

        Args:
            flights: Optional memoized flights for this target's user. If
                     omitted, the flights will be looked up.

        Returns:
            True if target may be considered an "actionable" submission.
        """
        if flights is None:
            flights = TakeoffOrLandingEvent.flights(self.user)

        actionable = False
        if len(flights) > 0:
            flight = flights[0]
            if flight.within(self.creation_time) and \
                flight.within(self.last_modified_time):
                actionable = True

        return self.actionable_override or actionable

    def interop_submission(self, missions=None):
        """Checks if Target meets Interoperability submission criteria.

        A target counts as being submitted over interoperability system if it
        was submitted and last updated while the team was on the mission clock.

        Args:
            missions: Optional memoized missions for this target's user. If
                     omitted, the missions will be looked up.

        Returns:
            True if target may be considered an "interoperability" submission.
        """
        if missions is None:
            missions = MissionClockEvent.missions(self.user)

        for mission in missions:
            if mission.within(self.creation_time) and \
                mission.within(self.last_modified_time):
                return True

        return False


class TargetEvaluator(object):
    """Evaluates submitted targets against real judge-made targets."""

    def __init__(self, submitted_targets, real_targets):
        """Creates an evaluation of submitted targets against real targets.

        Args:
            submitted_targets: List of submitted Target objects, all from
                               the same user.
            real_targets: List of real Target objects made by judges.

        Raises:
            AssertionError: not all submitted targets are from the same user.
        """
        self.submitted_targets = submitted_targets
        self.real_targets = real_targets

        if self.submitted_targets:
            self.user = self.submitted_targets[0].user
            for t in self.submitted_targets:
                if t.user != self.user:
                    raise AssertionError(
                        "All submitted targets must be from the same user")

            self.flights = TakeoffOrLandingEvent.flights(self.user)
            self.missions = MissionClockEvent.missions(self.user)

        self.matches = self.match_targets(submitted_targets, real_targets)
        self.unmatched = self.find_unmatched(submitted_targets, real_targets,
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
        """Evaluates the match if the two targets were to be paired.

        Args:
            submitted: The team submitted target. Must be one of
                self.submitted_targets.
            real: The real target made by the judges. Must be one of
                self.real_targets.
        Returns:
            auvsi_suas.proto.TargetEvaluation. The match evaluation.
        """
        target_eval = target_pb2.TargetEvaluation()
        target_eval.real_target = real.pk
        target_eval.submitted_target = submitted.pk
        target_eval.score_ratio = 0

        # Targets which are not the same type have no match value.
        if submitted.target_type != real.target_type:
            return target_eval
        # Targets which don't have an approved thumbnail have no value.
        if not submitted.thumbnail_approved:
            return target_eval

        # Compute values which influence score and are provided as feedback.
        target_eval.image_approved = submitted.thumbnail_approved
        if submitted.target_type == TargetType.emergent:
            target_eval.description_approved = submitted.description_approved
        target_eval.classifications_ratio = real.similar_classifications_ratio(
            submitted)
        if submitted.location:
            target_eval.geolocation_accuracy_ft = \
                    submitted.location.distance_to(real.location)
        target_eval.actionable_submission = submitted.actionable_submission(
            flights=self.flights)
        target_eval.autonomous_submission = submitted.autonomous
        target_eval.interop_submission = submitted.interop_submission(
            missions=self.missions)

        # Compute score.
        target_eval.classifications_score_ratio = \
                target_eval.classifications_ratio
        if target_eval.HasField('geolocation_accuracy_ft'):
            target_eval.geolocation_score_ratio = max(
                0, (float(settings.TARGET_LOCATION_THRESHOLD) -
                    target_eval.geolocation_accuracy_ft) /
                float(settings.TARGET_LOCATION_THRESHOLD))
        else:
            target_eval.geolocation_score_ratio = 0
        target_eval.actionable_score_ratio = \
                1 if target_eval.actionable_submission else 0
        target_eval.autonomous_score_ratio = \
                1 if target_eval.autonomous_submission else 0
        target_eval.interop_score_ratio = \
                1 if target_eval.interop_submission else 0
        target_eval.score_ratio = (
            (settings.CHARACTERISTICS_WEIGHT *
             target_eval.classifications_score_ratio) +
            (settings.GEOLOCATION_WEIGHT *
             target_eval.geolocation_score_ratio) +
            (settings.ACTIONABLE_WEIGHT * target_eval.actionable_score_ratio) +
            (settings.AUTONOMY_WEIGHT * target_eval.autonomous_score_ratio) +
            (settings.INTEROPERABILITY_WEIGHT *
             target_eval.interop_score_ratio))

        return target_eval

    def match_targets(self, submitted_targets, real_targets):
        """Matches the targets to maximize match value.

        Args:
            submitted_targets: List of submitted Target objects.
            real_targets: List of real Target objects made by judges.
        Returns:
            A map from submitted target to real target, and real target to
            submitted target, if they are matched.
        """
        # Create a bipartite graph from submitted to real targets with match
        # values (score ratio) as edge weights. Skip edges with no match value.
        g = nx.Graph()
        g.add_nodes_from(submitted_targets)
        g.add_nodes_from(real_targets)
        for submitted in submitted_targets:
            for real in real_targets:
                match_value = self.evaluate_match(submitted, real).score_ratio
                if match_value:
                    g.add_edge(submitted, real, weight=match_value)
        # Compute the full matching.
        return nx.algorithms.matching.max_weight_matching(g)

    def find_unmatched(self, submitted_targets, real_targets, matches):
        """Finds unmatched targets, filtering double-counts by autonomy.

        Args:
            submitted_targets: List of submitted Target objects.
            real_targets: List of real Target objects made by judges.
            matches: Map from submitted to real targets indicating matches.
        Returns:
            List of targets which are unmatched after filtering autonomy
            duplicates.
        """
        # Create a bipartite graph from unsubmitted to real targets with match
        # values (score ratio) as edge weights. Skip edges with no match value.
        # Skip edges if not inverse autonomy for existing match.
        remaining_targets = [t for t in submitted_targets if t not in matches]
        g = nx.Graph()
        g.add_nodes_from(remaining_targets)
        g.add_nodes_from(real_targets)
        for submitted in remaining_targets:
            for real in real_targets:
                match_value = self.evaluate_match(submitted, real).score_ratio
                inverted_autonomy = (
                    real in matches and
                    submitted.autonomous != matches[real].autonomous)
                if match_value and inverted_autonomy:
                    # We care about minimiznig unmatched, not match weight, so
                    # use weight of 1.
                    g.add_edge(submitted, real, weight=1)
        # Compute the matching to find unused objects.
        unused_match = nx.algorithms.matching.max_weight_matching(g)
        # Difference between remaining and unused is unmatched.
        return [t for t in remaining_targets if t not in unused_match]

    def evaluate(self):
        """Evaluates the submitted targets.

        Returns:
            auvsi_suas.proto.MultiTargetEvaluation.
        """
        multi_eval = target_pb2.MultiTargetEvaluation()
        # Compute match value.
        for real in self.real_targets:
            submitted = self.matches.get(real)
            if submitted:
                target_eval = multi_eval.targets.add()
                target_eval.CopyFrom(self.evaluate_match(submitted, real))
        if self.real_targets:
            multi_eval.matched_score_ratio = sum(
                [e.score_ratio for e in multi_eval.targets]) / len(
                    self.real_targets)
        else:
            multi_eval.matched_score_ratio = 0
        # Compute extra object penalty.
        multi_eval.unmatched_target_count = len(self.unmatched)
        multi_eval.extra_object_penalty_ratio = \
                (multi_eval.unmatched_target_count *
                        settings.EXTRA_OBJECT_PENALTY_RATIO)
        # Compute total score.
        multi_eval.score_ratio = (multi_eval.matched_score_ratio -
                                  multi_eval.extra_object_penalty_ratio)
        return multi_eval

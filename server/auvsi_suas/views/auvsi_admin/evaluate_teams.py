"""Admin automatic evaluation of teams view."""

import copy
import cStringIO
import csv
import json
import zipfile
from auvsi_suas.models import mission_evaluation
from auvsi_suas.views import logger
from auvsi_suas.views.decorators import require_superuser
from auvsi_suas.views.missions import mission_for_request
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.http import HttpResponseServerError
from django.utils.decorators import method_decorator
from django.views.generic import View
from google.protobuf import json_format


class EvaluateTeams(View):
    """Evaluates the teams and returns a zip file with CSV & JSON data.

    Zip file contains a master CSV and JSON file with all evaluation data.
    It also contains per-team JSON files for individual team feedback.
    """

    @method_decorator(require_superuser)
    def dispatch(self, *args, **kwargs):
        return super(EvaluateTeams, self).dispatch(*args, **kwargs)

    def pretty_json(self, json_str):
        """Generates a pretty-print json from any json."""
        return json.dumps(json.loads(json_str), indent=4)

    def csv_from_json(self, json_list):
        """Generates a CSV string from a list of rows as JSON strings."""
        csv_list = []
        for json_row in json_list:
            csv_dict = {}
            work_queue = [([], json.loads(json_row))]
            while len(work_queue) > 0:
                (cur_prefixes, cur_val) = work_queue.pop()
                if isinstance(cur_val, dict):
                    for (key, val) in cur_val.iteritems():
                        new_prefixes = copy.copy(cur_prefixes)
                        new_prefixes.append(str(key))
                        work_queue.append((new_prefixes, val))
                elif isinstance(cur_val, list):
                    for ix, val in enumerate(cur_val):
                        new_prefixes = copy.copy(cur_prefixes)
                        new_prefixes.append(str(ix))
                        work_queue.append((new_prefixes, val))
                else:
                    column_key = '.'.join(cur_prefixes)
                    csv_dict[column_key] = val
            csv_list.append(csv_dict)

        col_headers = set()
        for csv_dict in csv_list:
            col_headers.update(csv_dict.keys())
        col_headers = sorted(col_headers)

        csv_io = cStringIO.StringIO()
        writer = csv.DictWriter(csv_io, fieldnames=col_headers)
        writer.writeheader()
        for csv_dict in csv_list:
            writer.writerow(csv_dict)
        csv_output = csv_io.getvalue()
        csv_io.close()

        return csv_output

    def get(self, request):
        logger.info('Admin downloading team evaluation.')

        # Get the mission to evaluate a team for.
        mission, error = mission_for_request(request.GET)
        if error:
            logger.warning('Could not get mission to evaluate teams.')
            return error

        # Get the optional team to eval.
        users = None
        if 'team' in request.GET:
            try:
                team = int(request.GET['team'])
                users = [User.objects.get(pk=team)]
            except TypeError:
                return HttpResponseBadRequest('Team not an ID.')
            except User.DoesNotExist:
                return HttpResponseNotFound('Team not found.')

        # Get the eval data for the teams.
        mission_eval = mission_evaluation.evaluate_teams(mission, users)
        if not mission_eval:
            logger.warning('No data for team evaluation.')
            return HttpResponseServerError(
                'Could not get user evaluation data.')

        # Form Zip file.
        zip_io = cStringIO.StringIO()
        with zipfile.ZipFile(zip_io, 'w') as zip_file:
            zip_file.writestr(
                '/evaluate_teams/all.json',
                self.pretty_json(json_format.MessageToJson(mission_eval)))
            team_jsons = []
            for team_eval in mission_eval.teams:
                team_json = self.pretty_json(json_format.MessageToJson(
                    team_eval))
                zip_file.writestr('/evaluate_teams/teams/%s.json' %
                                  team_eval.team, team_json)
                team_jsons.append(team_json)

            zip_file.writestr('/evaluate_teams/all.csv',
                              self.csv_from_json(team_jsons))
        zip_output = zip_io.getvalue()
        zip_io.close()

        return HttpResponse(zip_output, content_type='application/zip')

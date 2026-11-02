"""Create narration facts solely from a validated team and replay item."""


def narration_facts(item, team):
    event = item['event']
    changes = {}
    for delta in item['deltas']:
        changes[delta['player']] = changes.get(delta['player'], 0) + delta['final_points']
    for player in (event['batter'], event['bowler'], (event['wicket'] or {}).get('player_out')):
        if player in team.xi and player not in changes:
            changes[player] = 0
    breakdown = [{
        'player': player, 'points': points,
        'role': 'captain' if player == team.captain else 'vice-captain' if player == team.vice_captain else 'regular',
    } for player, points in changes.items()]
    delta = sum(d['final_points'] for d in item['deltas'])
    event_description = (f"{event['wicket']['player_out']} dismissed {event['wicket']['kind']}; bowler {event['bowler']}"
                         if event['wicket'] else f"{event['batter']} scored {event['runs_batter']} runs off {event['bowler']}")
    return {'event': event_description, 'team_points_delta': f'{delta:+g}', 'breakdown': breakdown,
            'team_total': item['team_total_after'], 'score': item['match_state']['score'],
            'over': item['match_state']['over'], 'target': item['match_state']['target'], 'tag': item['tag']}

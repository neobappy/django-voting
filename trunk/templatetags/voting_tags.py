from django import template
from django.utils.html import escape

from voting.models import Vote

register = template.Library()

class ScoreForObjectNode(template.Node):
    def __init__(self, object, context_var):
        self.object = object
        self.context_var = context_var

    def render(self, context):
        try:
            self.object = template.resolve_variable(self.object, context)
        except template.VariableDoesNotExist:
            return ''
        context[self.context_var] = Vote.objects.get_score(self.object)
        return ''

class VoteByUserNode(template.Node):
    def __init__(self, user, object, context_var):
        self.user = user
        self.object = object
        self.context_var = context_var

    def render(self, context):
        try:
            self.user = template.resolve_variable(self.user, context)
            self.object = template.resolve_variable(self.object, context)
        except template.VariableDoesNotExist:
            return ''
        context[self.context_var] = Vote.objects.get_for_user(self.object, self.user)
        return ''

@register.tag(name='score_for_object')
def do_score_for_object(parser, token):
    """
    Retrieves the total score for an object and the number of votes
    it's received and stores them in a context variable which has
    ``score`` and ``num_votes`` properties.

    Example usage::

        {% score_for_object object as score %}

        {{ score.score }}point{{ score.score|pluralize }}
        after {{ score.num_votes }} vote{{ score.num_votes|pluralize }}
    """
    bits = token.contents.split()
    if len(bits) != 4:
        raise template.TemplateSyntaxError("'%s' tag takes exactly three arguments" % bits[0])
    if bits[2] != 'as':
        raise template.TemplateSyntaxError("second argument to '%s' tag must be 'as'" % bits[0])
    return ScoreForObjectNode(bits[1], bits[3])

@register.tag(name='vote_by_user')
def do_vote_by_user(parser, token):
    """
    Retrieves the ``Vote`` cast by a user on a particular object and
    stores it in a context variable. If the user has not voted, the
    context variable will be ``None``.

    Example usage::

        {% vote_by_user user object as vote %}
    """
    bits = token.contents.split()
    if len(bits) != 5:
        raise template.TemplateSyntaxError("'%s' tag takes exactly four arguments" % bits[0])
    if bits[3] != 'as':
        raise template.TemplateSyntaxError("third argument to '%s' tag must be 'as'" % bits[0])
    return VoteByUserNode(bits[1], bits[2], bits[4])

@register.simple_tag
def confirm_vote_message(object_description, vote_direction):
    """
    Creates an appropriate message asking the user to confirm the given vote
    for the given object description.

    Example usage::

        {% confirm_vote_message object.title direction %}
    """
    if vote_direction == 'clear':
        message = 'Confirm clearing your vote for <strong>%s</strong>.'
    else:
        message = 'Confirm <strong>%s</strong> vote for <strong>%%s</strong>.' % vote_direction
    return message % (escape(object_description),)

@register.filter
def vote_display(vote, arg=None):
    """
    Given a string mapping values for up and down votes, returns one
    of the strings according to the given ``Vote``:

    =========  =====================  =============
    Vote type   Argument               Outputs
    =========  =====================  =============
    ``+1``     ``"Bodacious,Bogus"``  ``Bodacious``
    ``-1``     ``"Bodacious,Bogus"``  ``Bogus``
    =========  =====================  =============

    If no string mapping is given, "Up" and "Down" will be used.

    Example usage::

        {{ vote|vote_display:"Bodacious,Bogus" }}
    """
    if arg is None:
        arg = 'Up,Down'
    bits = arg.split(',')
    if len(bits) != 2:
        return vote.vote # Invalid arg
    up, down = bits
    if vote.vote == 1:
        return up
    return down
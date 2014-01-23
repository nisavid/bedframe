"""Exceptions"""

__copyright__ = "Copyright (C) 2014 Ivan D Vasin"
__docformat__ = "restructuredtext"

import abc as _abc


class Error(RuntimeError):
    @property
    def displayname(self):
        return 'authentication error'


class BackendError(Error):

    """An authentication supplicant encountered an error in its backend

    :param supplicant:
        The authentication supplicant that encountered the error.
    :type supplicant:
        :class:`~bedframe.auth._connectors.Supplicant`

    :param error:
        The backend error.
    :type error: ~\ :obj:`str` or null

    """

    def __init__(self, supplicant, error=None, *args):
        super(BackendError, self).__init__(supplicant, error, *args)

    def __str__(self):
        message = 'authentication supplicant {} encountered an error in its'\
                   ' backend'\
                   .format(self.supplicant)
        if self.error:
            message += ': ' + str(self.error)
        return message

    @property
    def displayname(self):
        return 'authentication backend error'

    @property
    def error(self):
        return self.args[1]

    @property
    def supplicant(self):
        return self.args[0]


class InfiniteAffordances(Error):

    def __init__(self, affordances, infinite_components, message=None, *args):
        super(InfiniteAffordances, self).__init__(affordances,
                                                  infinite_components,
                                                  message, *args)

    def __str__(self):
        message = 'authentication affordances are infinite'
        if self.message:
            message += ': {}'.format(self.message)
        message += '; infinite components {}, affordances {}'\
                    .format(self.infinite_components, self.affordances)
        return message

    @property
    def affordances(self):
        return self.args[0]

    @property
    def displayname(self):
        return 'infinite authentication affordances'

    @property
    def infinite_components(self):
        return self.args[1]

    @property
    def message(self):
        return self.args[2]


class MissingTokens(ValueError):

    def __init__(self, names, message=None, *args):
        super(MissingTokens, self).__init__(names, message, *args)

    def __str__(self):
        message = 'missing authentication tokens {}'.format(self.names)
        if self.message:
            message += ': {}'.format(self.message)
        return message

    @property
    def displayname(self):
        return 'missing authentication tokens'

    @property
    def message(self):
        return self.args[1]

    @property
    def names(self):
        return self.args[0]


class NoValidTokensScanned(Error):

    """
    No valid authentication tokens were recognized by some authentication
    scanner

    :param scanner:
        The scanner.
    :type scanner: :class:`~bedframe.auth._connectors.Scanner`

    :param message:
        A message that describes which aspects of the authentication tokens
        were unrecognized.
    :type message: :obj:`str` or null

    """

    def __init__(self, scanner, message=None, *args):
        super(NoValidTokensScanned, self).__init__(scanner, message, *args)

    def __str__(self):
        message = 'no valid authentication tokens recognized by {}'\
                   .format(self.scanner)
        if self.message:
            message += ': {}'.format(self.message)
        return message

    @property
    def displayname(self):
        return 'no valid authentication tokens'

    @property
    def message(self):
        return self.args[1]

    @property
    def scanner(self):
        return self.args[0]


class RequiredParamValueNotSupported(Error):

    __metaclass__ = _abc.ABCMeta

    def __init__(self, value, message=None, handler=None,
                 supported_values=None, *args):
        super(RequiredParamValueNotSupported, self)\
         .__init__(value, message, handler, supported_values, *args)

    def __str__(self):
        message = 'required authentication {} value not supported'\
                   .format(self.param_name)
        if self.handler:
            message += ' by handler {!r}'.format(self.handler)
        if self.message:
            message += ': {}'.format(self.message)
        message += '; required {}'.format(self.value_str)
        if self.supported_values is not None:
            message += ', supported {}'.format(self.supported_values)
        return message

    @property
    def displayname(self):
        return 'required authentication {} value not supported'\
                .format(self.param_name)

    @property
    def handler(self):
        return self.args[2]

    @property
    def message(self):
        return self.args[1]

    @property
    def supported_values(self):
        return self.args[3]

    @_abc.abstractproperty
    def param_name(cls):
        pass

    @property
    def value(self):
        return self.args[0]

    @property
    def value_str(self):
        return unicode(self.value)


class RequiredParamValueSetNotSupported(RequiredParamValueNotSupported):

    __metaclass__ = _abc.ABCMeta

    @property
    def value_str(self):
        return 'any of {}'.format(self.value)


class RequiredAlgorithmNotSupported(RequiredParamValueNotSupported):
    @property
    def param_name(self):
        return 'algorithm'


class RequiredProvisionSetNotSupported(RequiredParamValueNotSupported):
    @property
    def param_name(self):
        return 'provision set'


class RequiredProvisionSetsNotSupported(RequiredParamValueSetNotSupported):
    @property
    def param_name(self):
        return 'provision sets'


class RequiredRealmNotSupported(RequiredParamValueNotSupported):
    @property
    def param_name(self):
        return 'realm'


class RequiredTokensNotSupported(RequiredParamValueNotSupported):

    __metaclass__ = _abc.ABCMeta

    @property
    def param_name(self):
        return self.tokens_type

    @_abc.abstractproperty
    def tokens_type(self):
        pass


class RequiredTokenSetsNotSupported(RequiredParamValueSetNotSupported,
                                    RequiredTokensNotSupported):
    __metaclass__ = _abc.ABCMeta

    @property
    def param_name(self):
        return '{}s'.format(self.tokens_type)


class RequiredInputNotSupported(RequiredTokensNotSupported):
    @property
    def tokens_type(self):
        return 'input'


class RequiredInputsNotSupported(RequiredTokenSetsNotSupported,
                                 RequiredInputNotSupported):
    pass


class RequiredOutputNotSupported(RequiredTokensNotSupported):
    @property
    def tokens_type(self):
        return 'output'


class RequiredOutputNotSupported(RequiredTokenSetsNotSupported,
                                      RequiredOutputNotSupported):
    pass


class UnsatisfiableAffordances(Error):

    def __init__(self, affordances, empty_components, message=None, *args):
        super(UnsatisfiableAffordances, self).__init__(affordances,
                                                       empty_components,
                                                       message, *args)

    def __str__(self):
        message = 'required authentication affordances are unsatisfiable'
        if self.message:
            message += ': {}'.format(self.message)
        message += '; empty components {}, affordances {}'\
                    .format(self.empty_components, self.affordances)
        return message

    @property
    def affordances(self):
        return self.args[0]

    @property
    def displayname(self):
        return 'unsatisfiable authentication affordances'

    @property
    def empty_components(self):
        return self.args[1]

    @property
    def message(self):
        return self.args[2]


class UnsuitableAgent(Error):

    """
    A chosen authentication agent was unsuitable for a specified operation

    :param str agenttype:
        A name that describes the type of agent.

    :param object agent:
        The agent.

    :param str operation:
        The operation for which the agent was unsuitable.

    :param realm:
        The authentication realm.
    :type realm: :obj:`str` or null

    :param provisions:
        The required security provisions.
    :type provisions:
        :class:`~bedframe.auth._provisions.ProvisionSet`

    :param message:
        A message that describes in what way the agent was unsuitable.
    :type message: :obj:`str` or null

    :param supported_realms:
        The agent's supported authentication realms.
    :type supported_realms:
        :class:`spruce.collections.uset \
                <spruce.collections._sets._universalizable.uset>`

    :param supported_provisionsets:
        The agent's sets of supported security provisions.
    :type supported_provisionsets:
        ~[:class:`~bedframe.auth._provisions.ProvisionSet`]

    """

    def __init__(self, agenttype, agent, operation, realm=None,
                 provisions=None, message=None, supported_realms=None,
                 supported_provisionsets=None, *args):
        super(UnsuitableAgent, self)\
         .__init__(agenttype,
                   agent,
                   operation,
                   realm,
                   provisions,
                   supported_realms,
                   tuple(sorted(supported_provisionsets or ())),
                   *args)

    def __str__(self):

        message = 'cannot {}; unsuitable {} {}'.format(self.operation,
                                                       self.agenttype,
                                                       self.agent)
        if self.realm:
            message += ' in authentication realm {}'.format(self.realm)
        if self.provisions:
            message += ', security provisions {}'.format(self.provisions)
        if self.message:
            message += ': {}'.format(self.message)

        supported_specs_messages = []
        if self.supported_realms:
            supported_specs_messages.append('supported realms {}'
                                             .format(self.supported_realms))
        elif self.supported_realms is not None:
            supported_specs_messages.append('no supported realms')
        if self.supported_provisionsets:
            supported_specs_messages\
             .append('supported security provision sets ({})'
                      .format(', '.join(str(provisions)
                                        for provisions
                                        in self.supported_provisionsets)))
        elif self.supported_provisionsets is not None:
            supported_specs_messages.append('no supported security provision'
                                            ' sets')
        if supported_specs_messages:
            message += '; ' + ', '.join(supported_specs_messages)

        return message

    @property
    def agent(self):
        return self.args[1]

    @property
    def agenttype(self):
        return self.args[0]

    @property
    def displayname(self):
        return 'unsuitable authentication agent'

    @property
    def message(self):
        return self._message

    @property
    def operation(self):
        return self.args[2]

    @property
    def provisions(self):
        return self.args[4]

    @property
    def realm(self):
        return self.args[3]

    @property
    def supported_provisionsets(self):
        return self.args[6]

    @property
    def supported_realms(self):
        return self.args[5]


class UnsuitableClerk(UnsuitableAgent):

    """
    A chosen authentication clerk was unsuitable for a specified operation

    """

    def __init__(self, agent, operation, realm=None, provisions=None,
                 message=None, supported_realms=None,
                 supported_provisionsets=None, *args):
        super(UnsuitableClerk, self)\
         .__init__('authentication clerk',
                   agent,
                   operation,
                   realm=realm,
                   provisions=provisions,
                   message=message,
                   supported_realms=supported_realms,
                   supported_provisionsets=supported_provisionsets,
                   *args)

    @property
    def displayname(self):
        return 'unsuitable authentication clerk'


class UnsuitableAuthenticator(UnsuitableAgent):

    """A chosen authenticator was unsuitable for a specified operation"""

    def __init__(self, agent, operation, realm=None, provisions=None,
                 message=None, supported_realms=None,
                 supported_provisionsets=None, *args):
        super(UnsuitableAuthenticator, self)\
         .__init__('authenticator',
                   agent,
                   operation,
                   realm=realm,
                   provisions=provisions,
                   message=message,
                   supported_realms=supported_realms,
                   supported_provisionsets=supported_provisionsets,
                   *args)

    @property
    def displayname(self):
        return 'unsuitable authenticator'


class UnsuitableSupplicant(UnsuitableAgent):

    """
    A chosen authentication supplicant was unsuitable for a specified
    operation

    """

    def __init__(self, agent, operation, realm=None, provisions=None,
                 message=None, supported_realms=None,
                 supported_provisionsets=None, *args):
        super(UnsuitableSupplicant, self)\
         .__init__('authentication supplicant',
                   agent,
                   operation,
                   realm=realm,
                   provisions=provisions,
                   message=message,
                   supported_realms=supported_realms,
                   supported_provisionsets=supported_provisionsets,
                   *args)

    @property
    def displayname(self):
        return 'unsuitable authentication supplicant'


class UnsupportedTokens(Error):

    """
    An authentication clerk was told to solicit an authentication token with
    parts that it does not support

    :param clerk:
        The clerk.
    :type clerk: :class:`~bedframe.auth._connectors.Clerk`

    :param message:
        A message that describes which aspects of the authentication token
        were unrecognized.
    :type message: :obj:`str` or null

    """

    def __init__(self, clerk, names, message=None, supported_names=None,
                 *args):
        super(UnsupportedTokens, self).__init__(clerk, names, message,
                                                    supported_names, *args)

    def __str__(self):
        message = 'authentication clerk {} does not support authentication'\
                   ' token parts {{{}}}'\
                   .format(self.clerk, ', '.join(self.names))
        if self.message:
            message += ': {}'.format(self.message)
        if self.supported_names:
            message += '; supported parts {{{}}}'\
                        .format(', '.join(self.supported_names))
        return message

    @property
    def clerk(self):
        return self.args[0]

    @property
    def displayname(self):
        return 'unsupported authentication token parts'

    @property
    def message(self):
        return self.args[2]

    @property
    def names(self):
        return self.args[1]

    @property
    def supported_names(self):
        return self.args[3]

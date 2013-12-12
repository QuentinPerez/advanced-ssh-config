# -*- coding: utf-8 -*-

import unittest

from advanced_ssh_config.advanced_ssh_config import AdvancedSshConfig
from . import set_config, prepare_config, DEFAULT_CONFIG


class TestAdvancedSshConfig(unittest.TestCase):

    def setUp(self):
        prepare_config()

    def test_load_advanced_ssh_config(self):
        advssh = AdvancedSshConfig()
        self.assertIsInstance(advssh, AdvancedSshConfig)

    def test_routing_simple(self):
        advssh = AdvancedSshConfig(hostname='test',
                                   port=23,
                                   verbose=True,
                                   dry_run=True)
        routing = advssh.get_routing()
        self.assertEqual(routing['port'], 23)
        self.assertEqual(routing['hostname'], 'test')
        self.assertEqual(routing['reallocalcommand'], [''])
        self.assertEqual(routing['gateways'], ['direct'])
        self.assertEqual(routing['verbose'], True)
        self.assertEqual(routing['proxy_type'], 'nc')
        self.assertEqual(routing['proxy_command'], ['nc', '-v', '-w', 180, '-G', 5, 'test', 23])

    def test_routing_hostname_in_config(self):
        contents = """
[test.com]
hostname = 1.2.3.4
port = 25
"""
        set_config(contents)
        advssh = AdvancedSshConfig(hostname='test.com',
                                   port=25,
                                   verbose=True,
                                   dry_run=True,
                                   configfiles=[DEFAULT_CONFIG])
        routing = advssh.get_routing()
        self.assertEqual(routing['port'], 25)
        self.assertEqual(routing['hostname'], '1.2.3.4')
        self.assertEqual(routing['proxy_type'], 'nc')
        self.assertEqual(routing['proxy_command'], ['nc', '-v', '-w', 180, '-G', 5, '1.2.3.4', 25])

    def test_routing_config_override(self):
        contents = """
[test.com]
port = 25
"""
        set_config(contents)
        advssh = AdvancedSshConfig(hostname='test.com',
                                   port=23,
                                   verbose=True,
                                   dry_run=True,
                                   configfiles=[DEFAULT_CONFIG])
        routing = advssh.get_routing()
        self.assertEqual(routing['port'], 23)
        self.assertEqual(routing['hostname'], 'test.com')
        self.assertEqual(routing['proxy_type'], 'nc')
        self.assertEqual(routing['proxy_command'], ['nc', '-v', '-w', 180, '-G', 5, 'test.com', 23])

    def test_routing_via_two_other_hosts(self):
        advssh = AdvancedSshConfig(hostname='aaa.com/bbb.com/ccc.com')
        routing = advssh.get_routing()
        self.assertEqual(routing['hostname'], 'aaa.com')
        self.assertEqual(routing['proxy_type'], 'nc')
        self.assertEqual(routing['gateways'], ['direct'])
        self.assertEqual(routing['proxy_command'], ['nc', '-w', 180, '-G', 5, 'aaa.com', 22])
        self.assertEqual(routing['gateway_route'], ['bbb.com', 'ccc.com'])

    def test_routing_via_two_other_hosts_with_config_one(self):
        contents = """
[ddd.com]
hostname = 1.2.3.4
port = 25
"""
        set_config(contents)
        advssh = AdvancedSshConfig(hostname='ddd.com/eee.com', configfiles=[DEFAULT_CONFIG])
        routing = advssh.get_routing()
        self.assertEqual(routing['hostname'], '1.2.3.4')
        self.assertEqual(routing['proxy_type'], 'nc')
        self.assertEqual(routing['gateways'], ['direct'])
        self.assertEqual(routing['proxy_command'], ['nc', '-w', 180, '-G', 5, '1.2.3.4', 25])
        self.assertEqual(routing['gateway_route'], ['eee.com'])


    def test_prepare_sshconfig_simple(self):
        contents = """
[test]
port = 25

[default]
port = 24
"""
        set_config(contents)
        advssh = AdvancedSshConfig(hostname='test', configfiles=[DEFAULT_CONFIG])
        config = advssh.prepare_sshconfig()
        self.assertEqual(len(config.keys()), 2)
        self.assertEqual(config['test'].host, 'test')
        self.assertEqual(config['test'].config, [('port', '25')])
        self.assertEqual(config['default'].host, 'default')
        self.assertEqual(config['default'].config, [('port', '24')])

    def test_prepare_sshconfig_multiline(self):
        contents = """
[test]
localforward = 1 2.3.4.5 6 \n 7 8.9.10.11 12
"""
        set_config(contents)
        advssh = AdvancedSshConfig(hostname='test', configfiles=[DEFAULT_CONFIG])
        config = advssh.prepare_sshconfig()
        self.assertEqual(config['test'].host, 'test')
        self.assertEqual(config['test'].config, [('localforward', '1 2.3.4.5 6'), ('localforward', '7 8.9.10.11 12')])

    def test_inherits(self):
        contents = """
[aaa]
hostname = 1.2.3.4
user = toto

[bbb]
inherits = aaa
port = 23
"""
        set_config(contents)
        advssh = AdvancedSshConfig(hostname='test', configfiles=[DEFAULT_CONFIG])
        config = advssh.config.full
        self.assertEqual(config['aaa'].clean_config['user'], 'toto')
        self.assertEqual('port' in config['aaa'].clean_config, False)
        self.assertEqual(config['bbb'].clean_config['user'], 'toto')
        self.assertEqual(config['bbb'].clean_config['port'], '23')

    def test_build_ssh_config(self):
        contents = """
[aaa]
hostname = 1.2.3.4
user = toto

[bbb]
inherits = aaa
port = 23
"""
        set_config(contents)
        advssh = AdvancedSshConfig(hostname='test', configfiles=[DEFAULT_CONFIG])
        config = advssh.prepare_sshconfig()
        arr = advssh.build_sshconfig()
        string = '\n'.join(arr)
        self.assertEquals(len(arr), 10)
        dest = """
Host aaa
  user toto
  # hostname aaa

Host bbb
  port 23
  user toto
  # inherits aaa
  # hostname bbb

"""
        self.assertEquals(string.strip(), dest.strip())



    # FIXME: test_inherits_noexists
    # FIXME: test_inherits_loop
    # FIXME: test_inherits_override
    # FIXME: test_prepare_sshconfig_with_hostname
    # FIXME: test_routing_override_config
    # FIXME: test_connect
    # FIXME: test_dryrun
    # FIXME: test_verbose
    # FIXME: test_alias

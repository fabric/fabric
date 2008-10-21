def setUp(self):
    pass
def test_cli_arg_parsing(self):
    tests = [
        ("abc", ("abc", {})),
        ("ab:c", ("ab", {'c':'c'})),
        ("a:b=c", ('a', {'b':'c'})),
        ("a:b=c,d=e", ('a', {'b':'c','d':'e'})),
    ]
    for cli, output in tests:
        self.assertEquals(fabric._parse_args([cli]), [output])

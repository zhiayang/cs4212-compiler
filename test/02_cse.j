// 02_cse.j

class Main
{
	Void main()
	{
		Int foo;
		Int bar;
		Int baz;
		Int a;
		Int b;
		Int x;

		foo = 69;
		bar = 420;
		baz = 1234;

		// this will result in _t0 = foo + bar; x = _t0 + baz.
		// this should let is CSE away both 'a' and 'b'.
		x = foo + bar + baz;
		a = foo + bar;

		if(1 < 69)
		{
			println("kekw");
		}
		else
		{
			println("sadge");
		}

		b = foo + bar;

		println(a);
		println(b);
		println(x);
	}
}

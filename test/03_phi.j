// 03_phi.j

class Main
{
	Void main()
	{
		Foo foo;

		println("start");

		foo = new Foo();
		if(foo.one() == 69 || foo.two() == 420)
		{
			println("success");
		}
		else
		{
			println("failure");
		}

		println("end");
	}
}


class Foo
{
	Int one()
	{
		println("one");
		return 69;
	}

	Int two()
	{
		println("you shouldn't see this");
		return 420;
	}
}

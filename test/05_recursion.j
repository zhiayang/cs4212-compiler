// 05_recursion.j

class Main
{
	Void main()
	{
		println(new Foo().sums(100));
	}
}

class Foo
{
	Int sums(Int num)
	{
		return sums(0, num);
	}

	Int sums(Int acc, Int num)
	{
		if(num == 0) { return acc; }
		else         { println(acc); return sums(acc + num, num - 1); }
	}
}

# loop.py
from typing import Optional, Iterator
import math

class loop:
    """
    Iterable that yields values from start -> stop.

    Parameters
    ----------
    start : number
        Start value.
    stop : number
        Stop value.
    points : int, optional
        Number of points (like numpy.linspace). If given, takes precedence over incr.
    incr : number, optional
        Step increment. If not given, defaults to +1 or -1 depending on start/stop.
    name : str, optional
        Friendly name (stored but not used for iteration).
    inclusive : bool, default True
        Whether to include `stop` (when using `incr`) or behave like linspace's endpoint.
    tol : float, default 1e-12
        Tolerance for floating point comparisons.
    """

    def __init__(self,
                 start: float,
                 stop: float,
                 points: Optional[int] = None,
                 incr: Optional[float] = None,
                 name: Optional[str] = None,
                 inclusive: bool = True,
                 tol: float = 1e-12):
        self.start = float(start)
        self.stop = float(stop)
        self.points = None if points is None else int(points)
        self.incr = None if incr is None else float(incr)
        self.name = name
        self.inclusive = bool(inclusive)
        self.tol = float(tol)

        if self.points is not None and self.points < 1:
            raise ValueError("points must be >= 1")
        if self.incr is not None and self.incr == 0:
            raise ValueError("incr must not be zero")
        # points takes precedence over incr if both provided
        if self.points is not None and self.incr is not None:
            self.incr = None

    def __iter__(self) -> Iterator[float]:
        """Return a fresh iterator (generator) so the object is re-iterable."""
        if self.points is not None:
            return self._iter_points()
        return self._iter_incr()

    def _iter_points(self) -> Iterator[float]:
        # behave like numpy.linspace with endpoint==inclusive
        n = self.points
        if n == 1:
            yield self.start
            return
        if self.inclusive:
            denom = n - 1
        else:
            denom = n
        step = (self.stop - self.start) / denom if denom != 0 else 0.0
        for i in range(n):
            yield self.start + i * step

    def _iter_incr(self) -> Iterator[float]:
        step = self.incr
        if step is None:
            # sensible default step
            step = 1.0 if self.start <= self.stop else -1.0

        cur = self.start

        # comparison lambdas with tolerance
        if step > 0:
            if self.inclusive:
                cmp = lambda a, b: a <= b + self.tol
            else:
                cmp = lambda a, b: a < b - self.tol
            while cmp(cur, self.stop):
                yield cur
                cur += step
        else:
            if self.inclusive:
                cmp = lambda a, b: a >= b - self.tol
            else:
                cmp = lambda a, b: a > b + self.tol
            while cmp(cur, self.stop):
                yield cur
                cur += step

    def to_list(self):
        """Return all values as a list."""
        return list(iter(self))

    def __len__(self):
        """Return length when possible:
           - if points specified -> points
           - if incr specified -> compute approximate count
           - otherwise compute using default incr (1 or -1)
        """
        if self.points is not None:
            return self.points

        step = self.incr
        if step is None:
            step = 1.0 if self.start <= self.stop else -1.0

        # if step moves the wrong direction -> 0
        if (self.start < self.stop and step <= 0) or (self.start > self.stop and step >= 0):
            return 0

        # compute number of steps (floor-based) and adjust for inclusive
        span = self.stop - self.start
        raw = span / step
        if raw < -self.tol:
            return 0
        # floor towards zero depending on sign of step
        n = int(math.floor(raw + self.tol)) + 1
        if self.inclusive:
            # if last point aligns closely with stop but raw was slightly smaller,
            # ensure we include the stop
            if math.isclose(self.start + (n - 1) * step, self.stop, rel_tol=0, abs_tol=self.tol):
                return n
            # else if exact stop isn't hit but would fit because of floating error, allow it
        return max(0, n)

    def __repr__(self):
        name = f" name='{self.name}'" if self.name is not None else ""
        if self.points is not None:
            return f"loop(start={self.start}, stop={self.stop}, points={self.points},{name})"
        return f"loop(start={self.start}, stop={self.stop}, incr={self.incr},{name})"




# # EXAMPLES:
# # usage_examples.py
# from vslab.loop import loop

# # linspace-style:
# l1 = loop(0, 1, points=5, name='lin')
# print(list(l1))   # [0.0, 0.25, 0.5, 0.75, 1.0]

# for val in l1:
#     print(val)


# # step-size style:
# l2 = loop(0, 1, incr=0.3, name='step')
# for v in l2:
#     print(v)
# # 0.0, 0.3, 0.6, 0.8999999999999999 (close to 0.9; endpoint included by default)


















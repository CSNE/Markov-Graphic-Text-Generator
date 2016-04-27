from time import time, sleep
class AnimatedValue:
    def __init__(self, value):
        self.value=value
        self.being_animated=False


    def animate(self, target, duration, ease_in, ease_out):
        if self.being_animated:#self value is currently being animated, need to commit the value before animating.
            self.value=self.getValue()

        self.target=target
        self.startTime=time()
        self.endTime=self.startTime+duration
        self.ease_in=ease_in
        self.ease_out=ease_out
        self.being_animated=True

    def set(self, target):
        self.value=target
        self.being_animated=False


    def isAnimating(self):
        return self.being_animated


    def getValue(self, currentTime):
        if (not self.being_animated):
            return self.value

        if (currentTime>self.endTime):
            self.value=self.target
            self.being_animated=False
            return self.value

        return quintic_ease(0,self.endTime-self.startTime,currentTime-self.startTime,self.value,self.target,self.ease_in,self.ease_out)





def quintic_ease(start,end,current,startVal,endVal,ease_in, ease_out):
        if (current>end):
            return endVal
        if (current<start):
            return startVal

        t=current-start
        d=end-start
        b=startVal
        c=endVal-startVal

        if ease_in and ease_out:
            t /= d/2
            if (t < 1):
                return c/2*t*t*t*t*t + b
            t -= 2
            return c/2*(t*t*t*t*t + 2) + b

        elif ease_out:
            t /= d
            t-=1
            return c*(t*t*t*t*t + 1) + b

        elif ease_in:
            t /= d
            return c*t*t*t*t*t + b

        else:
            return c*t/d + b

def main():
    av=AnimatedValue(10)
    av.animate(100, 10, (True, True))
    while True:
        print(av.getValue(time()))
        sleep(0.1)


if __name__=="__main__":
    main()
import random
l2=[chr(i) for i in range(ord('A'),ord('Z')+1)]
l3=[chr(i) for i in range(ord('a'),ord('z')+1)]
def genotp():
    otp=""
    for i in range(0,2):
        otp=otp+random.choice(l2)
        otp=otp+random.choice(l3)
        otp=otp+str(random.randint(0,9))
    return otp

#! /usr/bin/env python
#
#     bring up 2 dysh and 2 mpl plots. keep all 4 on screen so one can interact with them.
#     optionally save png's in --batch mode.
#
import sys

Qbatch = '--batch' in sys.argv       # cheap CLI parsing solution
Qdysh  = True                        # invalidate with --dysh
Qmpl   = True                        # invalidate with --mpl

if '--dysh' in sys.argv:
    Qdysh = False

if '--mpl' in sys.argv:
    Qmpl = False

print('Qbatch, Qdysh, Qmpl:',Qbatch, Qdysh, Qmpl)



if Qbatch and Qmpl:
    import matplotlib
    matplotlib.use("Agg")


if Qdysh:
    # bring up two plots from dysh
    from dysh.spectra.spectrum import Spectrum
    f = Spectrum.fake_spectrum()

    print("dysh figure 1")
    p1 = f.plot(xaxis_unit="MHz")
    print("dysh figure 2")    
    p2 = f.plot(xaxis_unit="km/s")

if Qmpl:
    # bring up 2 plots from matplotlib
    import matplotlib.pyplot as plt
    
    # figure 3
    print("mpl figure 3")
    plt.figure(3)
    plt.plot([0,3,1])
    if Qbatch:
        png = "fake_plot3.png"
        print(f"Written {png}")        
        plt.savefig(png)
    # figure 4
    print("mpl figure 4")
    plt.figure(4)
    plt.plot([1,2,4,2,1,3])

    # show
    if not Qbatch:
        plt.show()


if Qdysh:
    if Qbatch:
        png = "fake_plot1.png"
        p1.savefig(png)
        print(f"Written {png}")

        png = "fake_plot2.png"
        p2.savefig(png)
        print(f"Written {png}")
    else:
        # doing both means you can kill one and the other stays up
        # (but only if the mpl's are still up)
        p1.show(block=True)
        p2.show(block=True)


if not Qbatch and Qmpl:
    plt.show()
        


# Not running on IPython and trying to use the ShellGUI may result in unexpected behavior.

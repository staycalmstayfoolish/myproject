class _const:
    class ConstError(TypeError):
        pass

    class ConstCaseError(ConstError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            raise (self.ConstError, "Can't change const.%s" % name)
        self.__dict__[name] = value

const = _const()
const.TOTAL_ROUTE_CFG = 16
const.FP16_CNT = 64
const.LINE_LEN = 128
const.MEM2_BASE = 262144 #0x40000
const.MEM2_ROWS = 128
const.NET_ID = 0 #0,mlp; else, other nets
const.FOR_SIMU = 1

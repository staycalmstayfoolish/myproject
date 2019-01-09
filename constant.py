class _const:
    class ConstError(TypeError):
        pass

    class ConstCaseError(ConstError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__.keys():
            raise (self.ConstError, "Can't change const.%s" % name)
        #if not name.isupper():
            #raise (self.ConstCaseError, 'Const name "%s" is not all uppercase' % name)
        self.__dict__[name] = value

const = _const()
const.TOTAL_ROUTE_CFG = 9
const.FP16_CNT = 64
const.LINE_LEN = 128
const.MEM2_BASE = 262144 #0x40000
const.MEM2_ROWS = 128

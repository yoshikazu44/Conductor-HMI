"""
 共有メモリ

"""
from typing import Union
from enum   import IntEnum

class DataType(IntEnum):
    UNDEFINED = 0
    CHAR      = 1
    BOOL      = 2
    INT       = 3
    DOUBLE    = 4

class InterfaceData():

    def __init__(self, dataNo, dataType:DataType, value):
        
        self.dataNo:int   = dataNo
        self.dataType:int = dataType.value
        self.value:Union[bool, int, float] = value


SharedMemorySend = (InterfaceData(141, DataType.BOOL, 0), InterfaceData(142, DataType.BOOL, 0),
                    InterfaceData(143, DataType.BOOL, 0), InterfaceData(144, DataType.BOOL, 0),
                    InterfaceData(145, DataType.BOOL, 0), InterfaceData(146, DataType.INT,  0),
                    InterfaceData(148, DataType.INT,  0),
                   )


SharedMemoryRecv = (InterfaceData(  1, DataType.INT,    0),   InterfaceData(  2, DataType.INT,    0),
                    InterfaceData(  3, DataType.INT,    0),   InterfaceData(  4, DataType.DOUBLE, 0.0),
                    InterfaceData(  5, DataType.INT,    0),   InterfaceData(  6, DataType.INT,    0),
                    InterfaceData(  7, DataType.INT,    0),   InterfaceData(  8, DataType.DOUBLE, 0.0),
                    InterfaceData(  9, DataType.DOUBLE, 0.0), InterfaceData( 10, DataType.INT,    0),
                    InterfaceData(141, DataType.BOOL,   0),   InterfaceData(142, DataType.BOOL,   0),
                    InterfaceData(143, DataType.BOOL,   0),   InterfaceData(124, DataType.INT,    0),
                    InterfaceData(180, DataType.INT,    0),   InterfaceData(200, DataType.INT,    0), 
                    InterfaceData(201, DataType.INT,    0),   InterfaceData(203, DataType.INT,    0),
                    InterfaceData(205, DataType.BOOL,   0),   InterfaceData(206, DataType.INT,    0),
                    InterfaceData(207, DataType.INT,    0),   InterfaceData(208, DataType.INT,    0), 
                    InterfaceData(304, DataType.INT,    0),
                    )

update_flag = False #送信データ更新フラグ
exec_flag   = False #送信処理実行フラグ



def show_shared_memory_send():

    for data in SharedMemorySend:

        print("DataNo: {},\tValue: {}".format(data.dataNo, data.value))
    
    print('')

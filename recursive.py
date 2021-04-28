

class store:
    _type = 'store'
    _subtype = None
    def __repr__(self) -> str:
        return "{}_{} {}\n".format(self._subtype,self._type, self._data.__repr__())
    
    def __getstate__(self):
        return self._data

    def __setstate__(self,data):
        self._data = data

    def _has_list_descendant(self):
        if not getattr(self,'_terminal',False) \
            and len(self._data) \
            and getattr(self._data[0],'_type')=='store':
            return self._data[0]._is_list() or self._data[0]._has_list_descedant()
        return False

    def __bool__(self):
        return bool(self._data)   
    def _is_list(self):
        return getattr(self,'_subtype')=='list'

        
class list_store(store):
    _subtype = 'list'
#    _type = 'list_store'
    def __init__(self,data,terminal=False) -> None:
        self._data = tuple(data)
        self._terminal = terminal

    
    def __getattr__(self, name: str):
        if not len(self._data):
            return list_store([])
        first_item = self._data[0]
        if getattr(first_item, '_type', None) == 'store':
            return list_store([getattr(d,name) for d in self._data])
        return list_store(d[name] for d in self._data)

    def __getitem__(self, ind: int):
        # if self._has_list_descendant():
        #     return list_store([d[ind] for d in self._data])
        return self._data[ind]


    def sample(self, ind, squeeze=False):
        all =[d[ind] for d in self._data if d[ind]]
        if squeeze:
            return [a for a in all if a]
        return all


    def tolist(self):
        return list(self._data)

    def __dir__(self):
        if not len(self._data):
            return []
        first_item = self._data[0]
        if hasattr(first_item,'_subtype'):
            return dir(first_item) 
        return None

    @property
    def _(self):
        if not len(self._data):
            return None
        first_item = self._data[0]
        if hasattr(first_item,'_subtype'):
            return first_item._ 

    def __contains__(self,item):
        if not len(self._data):
            return False
        return item in self._data[0]


class dict_store(store):
    _subtype = 'dict'
    def __init__(self,data) -> None:
        self._data = dict(data)
    
    def __getattr__(self, name: str):
        #print("gatr")
        if name in self._data:
            return self._data[name]
        ret = dict_store({
        k: getattr(v,name, None) 
            for k,v in self._data.items()
                if getattr(v,name, None) is not None
                })   
        return ret
  

    def __getitem__(self, ind):
        print(  { k: v[ind] for k,v in self._data.items() if getattr(v,'_subtype',None) == 'list' })
        return dict_store(
            { k: v[ind] for k,v in self._data.items() if getattr(v,'_subtype',None) == 'list' }
            )

    def __dir__(self):
        return list(self._data.keys())+['_data','_terminal']

    @property
    def _(self):
        return ', '.join(self._data.keys())

    def __contains__(self,item):
        print("contains")
        return getattr(self,item) is not None    


class list_shorthand(list):
    maxlen=40
    def __repr__(self):
        full_str = list.__repr__(self)
        return  full_str[:self.maxlen] + ('...' if len(full_str)>self.maxlen else '')
    
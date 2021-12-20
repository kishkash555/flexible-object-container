from collections import Counter

class store:
    _type = 'store'
    _subtype = None
#    def __repr__(self) -> str:
#        return "{}_{} {}\n".format(self._subtype,self._type, self._data.__repr__())
    
    def __getstate__(self):
        ## used by pickle
        return self._data

    def __setstate__(self,data):
        ## used by pickle
        self._data = data
        nonnull = [d for d in self._data if d is not None]
        if len(nonnull):
            self._child_type = getattr(nonnull[0],'_type',None)
        else:
            self._child_type = None 

    def __bool__(self):
        return bool(self._data)   
    def _is_list(self):
        return getattr(self,'_subtype',None)=='list'
    def __len__(self):
        return len(self._data)   
    def keys(self):
        return Counter(self._keys())
      
class list_store(store):
    _subtype = 'list'
    _child_type = None
#    _type = 'list_store'
    def __init__(self,data) -> None:
        self._data = tuple(data)
        nonnull = [d for d in self._data if d is not None]
        if len(nonnull):
            self._child_type = getattr(nonnull[0],'_type',None)
        else:
            self._child_type = None 
        
    def __getattr__(self, name: str):
        if not len(self._data):
            return None
        if self._child_type =='store':
            ret = [getattr(d,name,None) for d in self._data] 
            if len(ret) and any([r is not None for r in ret]):
                return list_store(ret)
 
    def __getitem__(self, ind: int):
        # if self._has_list_descendant():
        #     return list_store([d[ind] for d in self._data])
        return self._data[ind]

    def __repr__(self) -> str:
        ld = len(self._data)
        rp = []
        if ld==0:
            rp.append('empty list_store')
        else:
            rp.append(f'list store with {ld} ')
            type_first_datum = type(self._data[0])
            if any(type(d)!= type_first_datum for d in self._data):
                rp.append('mixed-type elements')
            elif type_first_datum in (list_store, dict_store):
                rp.append(f'{self._data[0]._subtype} stores. first element:\n{self._data[0]!r}')
            else:
                rp.append(f'of {type_first_datum}')
            return ''.join(rp)


    def sample(self, ind, squeeze=False):
    # kept for backward compatibility
        all =[d[ind] for d in self._data if d[ind]]
        if squeeze:
            return [a for a in all if a]
        return all

    def _sample_leaf(self, ind):
        if self._child_type is not None:
            ret = [d._sample_leaf(ind) if getattr(d,'_type',None)=='store' else (None, True) for d in self._data]
            applied_sample_leaf = [b for _, b in ret] 
            if all(applied_sample_leaf):
                return list_store([a for a, _ in ret]), True
            if any(applied_sample_leaf):
                raise ValueError('Inconsitent hierarchy encountered in _sample_leaf')
        return (self._data[ind], True) if len(self._data)>ind else (None, True)
        

    def tolist(self):
        return list(self._data)


    def _keys(self):
        for d in self._data:
            if getattr(d,'_type',None)=='store':
                for k in d._keys():
                    yield '[*]'+k


    def __dir__(self):
        if not len(self._data):
            return ['_data']
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
            return dict_store({name: self._data[name]})
        ret = dict_store({
        k: getattr(v,name, None) 
            for k,v in self._data.items()
                if getattr(v,name, None) is not None
                })   
        return ret or None
  

    def __getitem__(self, ind):
        #print(  { k: v[ind] for k,v in self._data.items() if getattr(v,'_subtype',None) == 'list' })
        return dict_store(
            { k: v[ind] for k,v in self._data.items() if getattr(v,'_subtype',None) == 'list' }
            )
    

    def _keys(self):
        for k,v in self._data.items():
            if getattr(v,'_type',None)=='store':
                for kk in v._keys():
                    yield f'.{k}{kk}'
            else:
                yield f'.{k}'

    def __repr__(self):
        if len(self._data)==0:
            rp = ['empty dict store']
        else:
            rp = ['dict store with items: ']
        ld = len(self._data)==1  
        for k, v in self._data.items():
            is_store = getattr(v,'_type',None)=='store'
            rp.append(f'{k}: {v.__repr__() if ld and is_store else type(v)}')
        return ''.join(rp)


    def __dir__(self):
        return list(self._data.keys())+['_data']

    def __contains__(self,item):
        return getattr(self,item,None) is not None    

    def _sample_leaf(self, ind):
        if len(self._data)==1:
            k, v =list(self._data.items())[0]
            if getattr(v,'_type',None)=='store':
                sl, b = v._sample_leaf(ind)
                return dict_store({k: sl }), b
        return self, False
        
class list_shorthand(list):
    maxlen=40
    def __repr__(self):
        full_str = list.__repr__(self)
        return  full_str[:self.maxlen] + ('...' if len(full_str)>self.maxlen else '')
    
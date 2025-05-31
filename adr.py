import markdown
from bs4 import BeautifulSoup, NavigableString
from collections import defaultdict
import html
import os
import re
import zipfile

# estoy asumiendo que los títulos no se repiten. Si se llega a dar el caso que se repite, hay que cambiar los str por ids y listo.
class adr():
    
    def __init__(self, path,content=None): # TODO: Could be extended to accept instead of a file, a zip to process it, a static method to deal with the zip           
            
        def analyze_p(tt_s,code_t,save_content=True):
            for c in tt_s:
                if re_inic.search(c) is not None: # encontré algo
                    if code_t is None: # es un inicio de código
                        code_t = ''
                    else: # es un cierre, hay que guardar lo que hay
                        if save_content:
                            if self.path_separator.join(last_title_text) in self.content_raw:
                                self.content_raw[self.path_separator.join(last_title_text)][-1] += ' ' + code_t
                            else:
                                self.content_raw[self.path_separator.join(last_title_text)].append(code_t)

                        self.content_code[self.path_separator.join(last_title_text)].append(code_t)
                        code_t = None
                else:
                    if code_t is None: # parrafo comun
                        if save_content:
                            if self.path_separator.join(last_title_text) in self.content_raw:
                                self.content_raw[self.path_separator.join(last_title_text)][-1] += ' ' + c.replace('\n',' ')
                            else:
                                self.content_raw[self.path_separator.join(last_title_text)].append(c.replace('\n',' '))
                    else:
                        code_t += c # va adentro del código
            return code_t
        
        def process_code(code_t):
            if self.path_separator.join(last_title_text) in self.content_raw and self.content_raw[self.path_separator.join(last_title_text)][-1].endswith(':'):
                self.content_raw[self.path_separator.join(last_title_text)][-1] += ' ' + code_t.replace('\b',' ')
            else:
                self.content_raw[self.path_separator.join(last_title_text)].append(code_t.replace('\b',' '))
            self.content_code[self.path_separator.join(last_title_text)].append(code_t)
            code_t = None
            return code_t

        if path is None and content is None:
            raise Exception("Either path or content need to be specified")

        re_inic = re.compile("^[`|']{2,3}")
        re_fin = re.compile("[`|']{2,3}$")
        re_in = re.compile("[`']{2,3}")
        re_split = re.compile("([`']{2,3})")
        self.path_separator = ' #@# '
        
        last_title_type = []
        last_title_text = []
        code_t = None # sirve como flag de si se está en el medio de un fragmento de código
        
        self.name = os.path.basename(path)
        self.properties = dict()
        self.titles = defaultdict(list) # <nivel de título, [títulos a ese nivel]>
        self.hierarchy = defaultdict(list) # <título, [sub-títulos]>
        self.content_raw = defaultdict(list) # <título, [párrafos]> 
        self.content_code = defaultdict(list) # <título, [code]>  -- Fijate si necesitas o querés individualizar algo más
        # self.reverse_hierarchy = dict()

        if content is None:
            with open(path, "r", encoding="utf-8") as input_file:
                content = input_file.read()

        content = '\n'.join([x.strip() for x in content.split('\n')]) # just in case
        
        self.full_raw_content = content # TODO: we store the full content, so we don't have to rebuild it. The bad thing is that it is completely uncurated
        soup = BeautifulSoup(markdown.markdown(content), "html.parser")
        
        for s in soup:
            
            # print('---- line:',s)

            if isinstance(s, NavigableString) or s.name == 'hr':
                continue
            
            if not s.name.startswith('h') and len(last_title_type) == 0: # we have text without titles
                
                if str(s).startswith('<p><strong>') and ('>:' in str(s) or '> :' in str(s) or ':>' in str(s) or ': >' in str(s) or ':<' in str(s) or ': <' in str(s)):

                        ii = s.text.replace('\n',' ').strip().index(':') # we only care about the first one
                        self.content_raw[s.text.replace('\n',' ').strip()[0:ii].casefold()].append(s.text.replace('\n',' ').strip()[ii+1:].replace('\n',' '))
                        # self.hierarchy[s.text.replace('\n',' ').strip()[0:ii].casefold()] = []
                        last_title_text.append(s.text.replace('\n',' ').strip()[0:ii].casefold())
                        last_title_type.append('p')
                        self.titles['p'].append(s.text.replace('\n',' ').strip()[0:ii].casefold())
                        full_title_path = self.path_separator.join(last_title_text)
                else:
                    # está cayendo por acá la lista -- es un texto sin título, el título vacío no se agrega a la lista de títulos ni de ámbitos
                    self.content_raw[f'h0'].append(s.text.replace('\n',' '))
                    if 'h0' not in self.hierarchy:
                        self.hierarchy['h0'] = []

                continue
            
            # print(code_t,'::',s)

            if code_t is None and s.name.startswith('h'): # título que no aparece en el medio de un código por comentarios
                
                # print('++++++++++++++++++ code_t is None and we found a title')

                stext= s.text.strip()
                if re_inic.search(stext) is not None:
                    code_t = ''
                    continue
                
                full_title_path = stext.casefold() if stext.casefold()[-1] != ':' else stext.casefold()[0:-1] # we only want to remove the trailing : in titles
            
                while len(last_title_type) > 0 and last_title_type[-1] == 'p':
                    last_title_text = last_title_text[0:-1]
                    last_title_type = last_title_type[0:-1] 

                # acá analizamos los títulos
                if len(last_title_type) != 0: # si hubo título antes
                    # full_title_path = last_title_text + self.path_separator + full_title_path # avanzamos un nivel
                    
                    # print(last_title_text,'::',last_title_type,'::',s)

                    if s.name > last_title_type[-1]: # si el título es mayor, se agrega sin problema
                        self.hierarchy[self.path_separator.join(last_title_text)].append(full_title_path)
                        last_title_type.append(s.name) 
                        self.titles[s.name].append(self.path_separator.join(last_title_text) + self.path_separator + full_title_path)
                    
                    elif s.name == last_title_type[-1]: # mismo tipo de título
                        while len(last_title_type) > 0 and s.name == last_title_type[-1]:
                            last_title_text = last_title_text[0:-1]
                            last_title_type = last_title_type[0:-1]
                        # print('same title level!',last_title_type,last_title_text)
                        if len(last_title_text) > 0:
                            self.hierarchy[self.path_separator.join(last_title_text)].append(full_title_path) # TODO: Here, the list might be empty!
                            self.titles[s.name].append(self.path_separator.join(last_title_text) + self.path_separator + full_title_path)
                        else:
                            self.titles[s.name].append(full_title_path) # if there's no parent, we don't add it to hierarchy
                        last_title_type.append(s.name) 

                    elif s.name < last_title_type[-1]: # need to check how many we delete # 'h1' < 'h2' : True
                        while len(last_title_type) > 0 and s.name <= last_title_type[-1]:
                            last_title_text = last_title_text[0:-1]
                            last_title_type = last_title_type[0:-1] 

                        if len(last_title_text) > 0:
                            self.hierarchy[self.path_separator.join(last_title_text)].append(full_title_path) # TODO: Here, the list might be empty!
                            self.titles[s.name].append(self.path_separator.join(last_title_text) + self.path_separator + full_title_path)
                        else:
                            self.titles[s.name].append(full_title_path) # if there's no parent, we don't add it to hierarchy
                        last_title_type.append(s.name)                    
                    
                    # qué pasa si el último título fue un p?

                    last_title_text.append(full_title_path)
                    if self.path_separator.join(last_title_text) not in self.hierarchy:
                        self.hierarchy[self.path_separator.join(last_title_text)] = []
                    
                    # if last_title_type != '' and last_title_type != s.name: # si no están al mismo nivel, se lo agrego
                    #     self.hierarchy[last_title_text].append(full_title_path)
                    #     # self.reverse_hierarchy[full_title_path] = self.reverse_hierarchy.get(last_title_text,last_title_text)
                    #     last_title_type = s.name
                    #     last_title_text = last_title_text + self.path_separator + full_title_path
                    # else: # están al mismo nivel, entonces tienen el mismo padre
                    #     last_title_text = self.path_separator.join(last_title_text.split(self.path_separator)[0:-1])
                    #     # full_title_path = last_title_text + self.path_separator + full_title_path if last_title_text is not None else full_title_path

                    #     # last_title_text = full_title_path
                    #     self.hierarchy[last_title_text].append(full_title_path)
                    #     # self.reverse_hierarchy[full_title_path] = last_title_text

                    # self.titles[last_title_type].append(full_title_path) # lo agregamos a la estructura de títulos por jerarquía
                else: # first time, needs to be added
                    # print('----- no previous title',s)
                    last_title_type.append(s.name)
                    last_title_text.append(full_title_path) 
                    self.hierarchy[self.path_separator.join(last_title_text)] = []
                    self.titles[s.name].append(self.path_separator.join(last_title_text))
                    
                # print('=======================',last_title_type,'::',last_title_text)
           
            elif code_t is not None and s.name.startswith('h'): # estamos en medio de un fragmento de código que tiene que ser entendido como tal
                code_t += ' ' + '#' * int(s.name[1:]) + ' ' + s.text.strip()

                # print('---------------- code is not closed')
                # print(s)
                # print(code_t)
            
            elif s.name == 'ul' or s.name == 'ol': # lista de items o numérica           
                                
                # este es un caso MUY especial, el primero
                if last_title_type == 'h1': # encontré las properties o cualquier otro contenido que no es de properties
                    # guarda como properties todo lo que tenga :
                    pp = {x.text.split(':')[0].strip().casefold():x.text.split(':')[1].strip() for x in s.find_all('li') if ":" in x.text}
                    self.properties.update(pp)
                    listi = [x.text.strip().replace('\n',' ') for x in s.find_all('li') if ":" not in x.text]
                    if len(listi) > 0: # acá también se podría llegar a encontrar código
                        if len(self.content_raw[self.path_separator.join(last_title_text)]) == 0: 
                            self.content_raw[self.path_separator.join(last_title_text)].append(' '.join(listi).replace('\n',' '))
                        else:
                            self.content_raw[self.path_separator.join(last_title_text)][-1] += ' ' + ' '.join(listi).replace('\n',' ')
                    # print('____________________________________ AGREGANDO PROPERTIES AS TITLES')
                    if len(pp) > 0: # we add properties as if they were subheadings
                        for p,t in pp.items():
                            self.content_raw[last_title_text + self.path_separator + p].append(t)
                            self.hierarchy[self.path_separator.join(last_title_text)].append(p)
                            self.titles['p'].append(self.path_separator.join(last_title_text) + self.path_separator + p)
                      
                else: # estamos en el caso genérico en el que no es el h1
                    
                    # print('estamos en lista --------------------',full_title_path)
                    
                    temp_title = None
                    for x in s.find_all('li'):
                        # print(x)
                        if '<p><strong>' in str(x) and ('>:' in str(s) or '> :' in str(s) or ':>' in str(s) or ': >' in str(s) or ':<' in str(s) or ': <' in str(s)): # we have titles, again
                            ii = x.text.replace('\n',' ').strip().index(':')
                            temp_title = x.text.replace('\n',' ').strip()[0:ii].casefold()
                            self.content_raw[self.path_separator.join(last_title_text) + self.path_separator + temp_title].append(x.text.replace('\n',' ').strip()[ii+1:])
                            self.hierarchy[self.path_separator.join(last_title_text)].append(temp_title)
                            self.titles['p'].append(self.path_separator.join(last_title_text) + self.path_separator + temp_title)
                        else:
                            # print(last_title_text,'----------------',x,'----------- temp:',temp_title)
                            text = ' ' + re_inic.sub('',x.text).strip().replace('\n',' ')
                            tt_s = re_split.split(x.text)
                            code_t = analyze_p(tt_s,code_t,False)
                  
                            if len(self.content_raw[self.path_separator.join(last_title_text) if temp_title is None else self.path_separator.join(last_title_text) + self.path_separator + temp_title]) == 0:
                                self.content_raw[self.path_separator.join(last_title_text) if temp_title is None else self.path_separator.join(last_title_text) + self.path_separator + temp_title].append(text)
                            else:
                                self.content_raw[self.path_separator.join(last_title_text) if temp_title is None else self.path_separator.join(last_title_text) + self.path_separator + temp_title][-1] += ' ' + text.strip()

            # elif s.name == 'blockquote':
            #     print(' ----- TENEMOS UN BLOCKQUOTE',code_t is None)
            #     code_t = s.text if code_t is None else code_t + s.text

            else:
            # elif s.name == 'p': # tenemos un párrafo. Acá podría aparecer código entre comillas
                
                # print('--------- tenemos un párrafo que podría tener código')

                rr = s.text.strip().replace('\n',' ')
                
                starts_code = re_inic.search(rr) is not None
                ends_code = re_fin.search(rr) is not None
                in_code = re_in.search(rr) is not None
                
                # print(starts_code,ends_code,in_code) # all of this is false, but somehow, the code is defined

                if starts_code and ends_code and len(rr) > 3: # es todo código completo
                    code_t = re_inic.sub('',rr) 
                    code_t = process_code(code_t)
                    
                elif starts_code and ends_code: # hay solo indicador de inicio fin de código con longitud 3
                    # print('___________________ deberíamos estar acá')
                    if code_t is None:
                        code_t = ''
                    else: # cerramos un fragmento de código
                        # code_t += re_in.sub('',rr)
                        code_t = process_code(code_t)
                elif starts_code: # es un fragmento de comienzo de código
                    if code_t is None: 
                        code_t = rr[3:]
                    else:
                        code_t = process_code(code_t)
                elif ends_code: # es un fragmento de código que ya comenzó o puede arrancar para el próximo             
                    if code_t is not None: # efectivamente cierra
                        code_t += rr[0:-3]
                        code_t = process_code(code_t)
                    else: # si no había nada abierto, lo tiene que abrir
                        code_t = ''
                        self.content_raw[self.path_separator.join(last_title_text)].append(rr.replace('\b',' ').replace('\n',' ')[0:-3])
                        # tt_s = re_split.split(rr)
                        
                        # if len(tt_s) == 1:
                        #     self.content_raw[self.path_separator.join(last_title_text)].append(rr.replace('\b',' ').replace('\n',' '))
                        # else: # hay algún fragmento de código metido en el medio
                        #     code_t = analyze_p(tt_s,code_t)
                
                elif in_code: # hay algo de código dando vueltas, debería estar abierto o no... no sabemos
                    # print('---------------------------- encontramos algo de código apertura/cierre en el medio del párrafo',code_t is None) 
                    # print(len(re_in.split(s.text)))
                    # print(re_in.split(s.text))
                    
                    xx = re_in.split(s.text) # TODO: Qué pasa si hay una longitud mayor a 2?

                    if code_t is not None: # código está abierto, lo cerramos
                        code_t += xx[0]
                        code_t = process_code(code_t)
                        self.content_raw[self.path_separator.join(last_title_text)].append(xx[1].replace('\b',' '))

                    else: # abrimos código
                        self.content_raw[self.path_separator.join(last_title_text)].append(xx[0].replace('\b',' '))
                        code_t = xx[1]
                    # Need to add to content raw the part that is code

                else: # era un párrafo común

                    # print('++++++++++++++ era un párrafo común?')

                    # párrafo normal o párrafo con tratamiento de título?
                    if str(s).startswith('<p><strong>') and ('>:' in str(s) or '> :' in str(s) or ':>' in str(s) or ': >' in str(s) or ':<' in str(s) or ': <' in str(s)):
                        ii = s.text.replace('\n',' ').strip().index(':') # we only care about the first one

                        if last_title_type[-1] == 'p':
                            last_title_text = last_title_text[0:-1]
                            last_title_type = last_title_type[0:-1]
                        
                        if len(last_title_text) > 0:
                            self.content_raw[self.path_separator.join(last_title_text) + self.path_separator + s.text.replace('\n',' ').strip()[0:ii].casefold()].append(s.text.replace('\n',' ').strip()[ii+1:].replace('\n',' '))
                            self.hierarchy[self.path_separator.join(last_title_text)].append(s.text.replace('\n',' ').strip()[0:ii].casefold())
                        else:
                            self.content_raw[s.text.replace('\n',' ').strip()[0:ii].casefold()].append(s.text.replace('\n',' ').strip()[ii+1:].replace('\n',' '))
                        # here, teníamos título de los anteriores -- si acá sumo, luego hay que bajar
                        
                        last_title_text.append(s.text.replace('\n',' ').strip()[0:ii].casefold())
                        last_title_type.append('p') 
                        self.titles['p'].append(self.path_separator.join(last_title_text))
                        
                        # last_title_text = full_title_path + self.path_separator + s.text.replace('\n',' ').strip()[0:ii].casefold()
                            # last_title_type = 'h2' if last_title_type == 'h1' else 'h3' if last_title_type == 'h2' else 'h4'
                        # else: # si no hay un título previo, asumimos que está en el primer nivel
                        #     self.content_raw[s.text.replace('\n',' ').strip()[0:ii].casefold()].append(s.text.replace('\n',' ').strip()[ii+1:].replace('\n',' '))
                        #     self.hierarchy[s.text.replace('\n',' ').strip()[0:ii].casefold()] = []
                        #     last_title_text = s.text.replace('\n',' ').strip()[0:ii].casefold()
                        #     full_title_path = last_title_text
                        
                        
                        # print('xx________________________',full_title_path)
                        # print('xx________________________',last_title_type)
                        # print('xx________________________',last_title_text)
                        continue
                    
                    if code_t is not None: # si es un párrafo normal, pero en medio de un código, se guarda como código que ya va a terminar TODO: Técnicamente el análisis se podría hacer acá?
                        code_t += re_in.sub('',rr)
                    else: # code_t is None
                        # por más que no empiece ni termine como código, acá podría haber un inicio de código que queda camuflado
                        tt_s = re_split.split(rr)
                        
                        if len(tt_s) == 1:
                            self.content_raw[self.path_separator.join(last_title_text)].append(rr.replace('\b',' '))
                        else: # hay algún fragmento de código metido en el medio
                            code_t = analyze_p(tt_s,code_t)
                            
                    codes = s.find_all('code') # esto funciona solo cuando el código tiene el tag de código, pero no cuando ponen el código con '''XX'''
                    if len(codes) > 0:
                        self.content_code[full_title_path].extend([html.unescape(x.text.strip()).replace('\n',' ') for x in codes])

    def get_hierarchy(self):
        return self.hierarchy

    def get_content(self,title=None):
        if title is None:
            return self.content_raw
        return self.content_raw.get(title,[])
        
    def get_titles(self,level=None):
        if level is None:
            return [x for v in self.titles.values() for x in v]
        return self.titles.get(level,[])
    
    def get_code(self,title=None):
        if title is None:
            return self.content_code
        return self.content_code.get(title,[])
    
    def get_properties(self,key=None):
        if key is None:
            return self.properties        
        return self.properties.get(key,None)
    
    def get_name(self):
        return self.name

    def get_content_str(self,title=None):
        cc = self.get_content(title)
        if type(cc) is defaultdict:
            cc = cc.values() # lista de listas
            cc = [x for a in cc for x in a]  
        return ' '.join(cc)
    
    def get_content_no_code(self,title=None):
        if title is not None:
            if title not in self.content_raw:
                return []
            clean = []
            code = self.get_code(title)
            code = [x for x in code if len(x.split(' ')) > 1] # para controlar que no sean palabras sueltas
            for x in self.content_raw[title]:
                for c in code:
                    x = x.replace(c,'')
                x = x.strip()
                if len(x) > 1:
                    clean.append(x)
            return clean
        dict_clean = {}
        for t in self.get_titles(): 
            dict_clean[t] = self.get_content_no_code(t)
        return dict_clean
    
    def get_content_no_code_str(self,title=None): 
        cc = self.get_content_no_code(title)
        if type(cc) is dict:
            cc = cc.values() # lista de listas
            cc = [x for a in cc for x in a]  
        return ' '.join(cc)
    
    def get_full_raw_content(self):
        return self.full_raw_content

    def get_full_content(self):
    # Recursive function to walk the hierarchy
        def walk_hierarchy(title,depth=1):
            content = []
            if len(title) > 0:
                content.append('#'*depth + ' ' + title.split(self.path_separator)[-1])
                
            if title in self.content_raw:
                content.extend(self.content_raw[title])
                    
            for child in self.hierarchy.get(title, []):
                content.extend(walk_hierarchy(title + self.path_separator + child,depth+1))

            return content

        full_content = []
        all_children = {child for children in self.hierarchy.values() for child in children}

        # Start with top-level titles
        for top_title in self.hierarchy:
            # Only start recursion from root-level entries (i.e., those not referenced as children)
            if top_title.split(self.path_separator)[-1] not in all_children:
                full_content.extend(walk_hierarchy(top_title))

        return '\n'.join(full_content)
    
    def get_decision(self): # need to be searched in hierarchy

        def check_subsections(dicti,depth=2):
            # print('check_subsections:',dicti)
            ss = []
            ch = set()
            for t, c in dicti.items(): # from all titles -- it should be all titles with decision in the context_raw ?
                for x in c:
                    t_ = t + self.path_separator + x
                    # print(t_, t_ in self.content_raw)
                    ss.append('#'*depth + ' ' + x)
                    ss.extend(self.content_raw[t_])
                    aa = check_subsections({t_ : self.hierarchy.get(t_,[])},depth+1)
                    ss.extend(aa[0])
                    ch.update(aa[1])
                    ch.add(t_)
            return ss,ch
        
        dd = []
        checked = set()
        for t, c in self.hierarchy.items(): # from all titles -- it should be all titles with decision in the context_raw ?

            if t in checked:
                continue
            
            xx = [x for x in c if x == 'decision'.casefold() or x.strip().startswith('decision'.casefold()) or x.strip().startswith('final decision'.casefold())]
            # print('xx:',xx)

            if t == 'decision'.casefold() or t.strip().startswith('decision'.casefold()) or t.strip().startswith('final decision'.casefold()): #  or len(xx) > 0 # TODO: esto es para agregar el texto del padre de donde se encontró el decision -- not sure about this, podría terminar agregando más cosas de las que queremos si se hace jerárquico
                # print(t, t in self.content_raw)
                dd.extend(self.content_raw[t])
                aa = check_subsections({t : self.hierarchy.get(t,[])})
                dd.extend(aa[0])
                checked.update(aa[1]) 
                checked.add(t)

            for x in xx:
                t_ = t + self.path_separator + x
                # print(t_, t_ in self.content_raw)
                dd.append('# ' + x)
                dd.extend(self.content_raw[t_])
                aa = check_subsections({t_ : self.hierarchy.get(t_,[])})
                dd.extend(aa[0])
                checked.update(aa[1])
        # print(dd)
        return '\n'.join(dd)

    def get_title(self): # it should be the only title that it doesn't appear on the right side
        # TODO: Check if this works!
        # if 'h1' in self.titles:
        #     if len(self.titles['h1']) == 1 or self.hierarchy is None:
        #         return self.titles['h1'][0]
        
        all_children = {child for children in self.hierarchy.values() for child in children}
        for top_title in self.hierarchy:
            # Only start recursion from root-level entries (i.e., those not referenced as children)
            if top_title not in all_children:
                return top_title
            
        for x in ['h1','h2','h3','h4','p']:
            if x in self.titles and len(self.titles[x]) > 0:
                return self.titles[x][0]
        
        return None   

    @staticmethod
    def read_zipfile(dir_path='./',zip_name=None,inner_path=''):
        adrs_dict = defaultdict(defaultdict(dict).copy)

        with zipfile.ZipFile(data_dir + zip_name) as z:
            for full_path in tqdm(z.namelist()):
                if full_path.endswith('/') or inner_path not in full_path:
                    continue
                full_path = full_path.replace(inner_path,'')
                full_path = full_path.split('/')
                
                if len(full_path) != 3:
                    continue
                
                org,project,adr_name = full_path
                print(full_path)
                with z.open(inner_path + f'{org}/{project}/{adr_name}') as f:
                    content = f.read().decode('utf8')
                    try:
                        adrs_dict[org][project][adr_name] = adr(path=inner_path + f'{org}/{project}/{adr_name}',content=content)
                    except ValueError:
                            print('Value ERROR -- ',inner_path + org + '/' + project + '/' + adr_name)
        return adrs_dict
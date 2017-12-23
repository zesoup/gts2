
CREATE OR REPLACE FUNCTION renderbackend_tracks( _posx numeric, _posy numeric , pixpermapx numeric, pixpermapy numeric,  zoomx float, zoomy float, transparency bool default False )
	RETURNS void
	language plpythonu
	as $$
                                    try:
                                        import cairo
                                        import pygame
                                        import json
                                        import traceback


                                        plan = plpy.prepare("SELECT osm_id, st_asgeojson(a.way) js,tags,zlevel,color, width  wdth,_width wdthh,key, value, z_order  FROM all_render a  WHERE  st_dwithin(a.way, ST_SetSRID(ST_MakePoint($1,$2),3857),$3) ORDER BY zlevel asc, osm_id desc", ["numeric","numeric","numeric"] )
                                        cursor = plpy.cursor( plan, [float(_posx)+(float(pixpermapx)*zoomx*0.5), float(_posy)+(float(pixpermapy)*zoomy*0.5), float(pixpermapx)*float(zoomx)*1.] )
                                        
                                        rasterimg = pygame.Surface( (pixpermapx, pixpermapy), pygame.SRCALPHA, 32)
                                        pixels = pygame.surfarray.pixels2d( rasterimg ) 
                                        surface_cairo = cairo.ImageSurface.create_for_data (pixels.data, cairo.FORMAT_ARGB32, pixpermapx, pixpermapy)

                                        ctx = cairo.Context( surface_cairo) 


                                        if not transparency:
                                                rasterimg.fill((10,70,30,255))

                                        #for item in a:
                                        while True:
                                                items = cursor.fetch(1)
                                                if not items:
                                                        break
						item = items[0]
                                                #(qid, qway, qtags, qzlevel, qcolor,qlwidth, qwidth, qkey, qvalue, zorder) =item
                                                qid = item['osm_id']
                                                qway = item['js']
                                                qtags = item['tags']
                                                qzlevel = item['zlevel']
                                                qcolor = item['color']
                                                #print item['wdth']
                                                #print item['wdthh']
                                                #print "^^^^^^"
                                                qlwidth =  item['wdth']
                                                qwidth = item['wdthh']
                                                qkey = item['key']
                                                qvalue = item['value']
                                                zorder = item['z_order']
                                                jsonway = json.loads(qway)
                                                exec(qcolor)
                                                if qwidth == None:
                                                        qwidth = 0
                                                if jsonway['type']=='Polygon':
                                                        for pt in jsonway['coordinates']:
                                                                g=[]
                                                                for grp in pt:
                                                                        try:
                                                                                #agrp=recalcpos(grp,( _posx,_posy), (zoomx, zoomy) )
                                                                                #g.append( (float(agrp[0]),float(agrp[1])))
                                                                                g.append(( (grp[0]-float(_posx))/zoomx , (grp[1]-float(_posy))/zoomy))
                                                                        except Exception as e:
                                                                                print e
                                                                                print "could not parse"
                                                                if len(g) <= 3:
                                                                        print "skipping"
                                                                        continue
                                                                w = float(qwidth)/float(zoomx)

                                                                ctx.set_source_rgb( float(color[0])/255.0, float(color[1])/255.0, float(color[2])/255.0)
                                                                ctx.set_line_width(int(float(w) ) ) # DAFUQ? CASTMANIA!
                                                                ctx.move_to( g[0][0], g[0][1] )
                                                                for p in g[1:]:
                                                                        ctx.line_to( p[0], p[1] )
                                                                ctx.close_path()
                                                                if w==0:
                                                                        ctx.fill()
                                                                ctx.stroke()
                                                if jsonway['type']=='LineString':
                                                        w = float(qwidth)/zoomx
                                                        try:
                                                                if qlwidth != None:
                                                                        qlwidth=qlwidth.replace(',','.')
                                                                        qlwidth=qlwidth.replace('m','')
                                                                        qlwidth=qlwidth.strip()
                                                                        w=float(qlwidth)+qwidth
                                                                        w=w/zoomx
                                                        except Exception as e:
                                                                print e
                                                                print "Meh, broken"
                                                        g=[]
                                                        for grp in jsonway['coordinates']:
                                                                try:
                                                                        #agrp=recalcpos(grp, (_posx,_posy), (zoomx,zoomy) )
                                                                        #g.append( (float(agrp[0]),float(agrp[1])))
                                                                        g.append( ((grp[0]-float(_posx ))/zoomx , (grp[1]-float(_posy))/zoomy))
                                                                except Exception as e:
                                                                        print e
                                                                        traceback.print_exc()
                                                                        #print "could not parse"
                                                        if len(g) < 2:
                                                                print "skipping"
                                                                continue
                                                        ctx.set_source_rgb( float(color[0])/255.0, float(color[1])/255.0, float(color[2])/255.0)
                                                        ctx.set_line_width(int(float(w) ) ) # DAFUQ? CASTMANIA!
                                                        ctx.move_to( g[0][0], g[0][1] )
                                                        for p in g[1:]:
                                                                ctx.line_to( p[0], p[1] )
                                                        ctx.stroke()

                                        #q.put( pygame.image.tostring(rasterimg, 'RGBA') )
					plan = plpy.prepare("INSERT INTO frontendcache(x,y,zoom,data) VALUES ($1,$2,$3,$4) on conflict do nothing", ["numeric", "numeric", "numeric", "text"])
					plpy.execute(plan, [_posx, _posy, zoomx, pygame.image.tostring(rasterimg, 'RGBA').encode('hex')   ] ) 
                                        return
                                    except Exception as e:
                                        print e
                                        traceback.print_exc()
                                        #print "RENDERISSUE"
                                        return
$$;




CREATE OR REPLACE FUNCTION renderbackend( _posx numeric, _posy numeric , pixpermapx numeric, pixpermapy numeric,  zoomx float, zoomy float, transparency bool default False )
	RETURNS void
	language plpythonu
	as $$
                                    try:
                                        import cairo
                                        import pygame
                                        import json
                                        import traceback


                                        plan = plpy.prepare("SELECT osm_id, st_asgeojson(a.way) js,tags,zlevel,color, width  wdth,_width wdthh,key, value, z_order  FROM all_render a  WHERE  st_dwithin(a.way, ST_SetSRID(ST_MakePoint($1,$2),3857),$3) ORDER BY zlevel asc, osm_id desc", ["numeric","numeric","numeric"] )
                                        cursor = plpy.cursor( plan, [float(_posx)+(float(pixpermapx)*zoomx*0.5), float(_posy)+(float(pixpermapy)*zoomy*0.5), float(pixpermapx)*float(zoomx)*1.] )
                                        
                                        rasterimg = pygame.Surface( (pixpermapx, pixpermapy), pygame.SRCALPHA, 32)
                                        pixels = pygame.surfarray.pixels2d( rasterimg ) 
                                        surface_cairo = cairo.ImageSurface.create_for_data (pixels.data, cairo.FORMAT_ARGB32, pixpermapx, pixpermapy)

                                        ctx = cairo.Context( surface_cairo) 


                                        if not transparency:
                                                rasterimg.fill((10,70,30,255))

                                        #for item in a:
                                        while True:
                                                items = cursor.fetch(1)
                                                if not items:
                                                        break
						item = items[0]
                                                #(qid, qway, qtags, qzlevel, qcolor,qlwidth, qwidth, qkey, qvalue, zorder) =item
                                                qid = item['osm_id']
                                                qway = item['js']
                                                qtags = item['tags']
                                                qzlevel = item['zlevel']
                                                qcolor = item['color']
                                                #print item['wdth']
                                                #print item['wdthh']
                                                #print "^^^^^^"
                                                qlwidth =  item['wdth']
                                                qwidth = item['wdthh']
                                                qkey = item['key']
                                                qvalue = item['value']
                                                zorder = item['z_order']
                                                jsonway = json.loads(qway)
                                                exec(qcolor)
                                                if qwidth == None:
                                                        qwidth = 0
                                                if jsonway['type']=='Polygon':
                                                        for pt in jsonway['coordinates']:
                                                                g=[]
                                                                for grp in pt:
                                                                        try:
                                                                                #agrp=recalcpos(grp,( _posx,_posy), (zoomx, zoomy) )
                                                                                #g.append( (float(agrp[0]),float(agrp[1])))
                                                                                g.append(( (grp[0]-float(_posx))/zoomx , (grp[1]-float(_posy))/zoomy))
                                                                        except Exception as e:
                                                                                print e
                                                                                print "could not parse"
                                                                if len(g) <= 3:
                                                                        print "skipping"
                                                                        continue
                                                                w = float(qwidth)/float(zoomx)

                                                                ctx.set_source_rgb( float(color[0])/255.0, float(color[1])/255.0, float(color[2])/255.0)
                                                                ctx.set_line_width(int(float(w) ) ) # DAFUQ? CASTMANIA!
                                                                ctx.move_to( g[0][0], g[0][1] )
                                                                for p in g[1:]:
                                                                        ctx.line_to( p[0], p[1] )
                                                                ctx.close_path()
                                                                if w==0:
                                                                        ctx.fill()
                                                                ctx.stroke()
                                                if jsonway['type']=='LineString':
                                                        w = float(qwidth)/zoomx
                                                        try:
                                                                if qlwidth != None:
                                                                        qlwidth=qlwidth.replace(',','.')
                                                                        qlwidth=qlwidth.replace('m','')
                                                                        qlwidth=qlwidth.strip()
                                                                        w=float(qlwidth)+qwidth
                                                                        w=w/zoomx
                                                        except Exception as e:
                                                                print e
                                                                print "Meh, broken"
                                                        g=[]
                                                        for grp in jsonway['coordinates']:
                                                                try:
                                                                        #agrp=recalcpos(grp, (_posx,_posy), (zoomx,zoomy) )
                                                                        #g.append( (float(agrp[0]),float(agrp[1])))
                                                                        g.append( ((grp[0]-float(_posx ))/zoomx , (grp[1]-float(_posy))/zoomy))
                                                                except Exception as e:
                                                                        print e
                                                                        traceback.print_exc()
                                                                        #print "could not parse"
                                                        if len(g) < 2:
                                                                print "skipping"
                                                                continue
                                                        ctx.set_source_rgb( float(color[0])/255.0, float(color[1])/255.0, float(color[2])/255.0)
                                                        ctx.set_line_width(int(float(w) ) ) # DAFUQ? CASTMANIA!
                                                        ctx.move_to( g[0][0], g[0][1] )
                                                        for p in g[1:]:
                                                                ctx.line_to( p[0], p[1] )
                                                        ctx.stroke()

                                        #q.put( pygame.image.tostring(rasterimg, 'RGBA') )
					plan = plpy.prepare("INSERT INTO frontendcache(x,y,zoom,data) VALUES ($1,$2,$3,$4) on conflict do nothing", ["numeric", "numeric", "numeric", "text"])
					plpy.execute(plan, [_posx, _posy, zoomx, pygame.image.tostring(rasterimg, 'RGBA').encode('hex')   ] ) 
                                        return
                                    except Exception as e:
                                        print e
                                        traceback.print_exc()
                                        #print "RENDERISSUE"
                                        return
$$;



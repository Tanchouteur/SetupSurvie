"""Generate a tiny fictional archive; libzim remains optional outside this helper."""
def create(path,*,media=None,extra=False,with_tracks=True,extension='webm'):
    if extension not in ('webm','mp4'):raise ValueError('Synthetic fixture format required')
    from libzim.writer import Creator,Item,StringProvider,Hint
    class Resource(Item):
        def __init__(self,path,mime,text):super().__init__();self.path=path;self.mime=mime;self.text=text
        def get_path(self):return self.path
        def get_title(self):return 'Fictional video course' if self.mime=='text/html' else self.path
        def get_mimetype(self):return self.mime
        def get_contentprovider(self):return StringProvider(self.text)
        def get_hints(self):return {Hint.FRONT_ARTICLE:self.mime=='text/html'}
    with Creator(path).config_indexing(True,'eng') as creator:
        for key,value in {'Title':'Fictional video inventory','Name':'video-fixture','Language':'eng'}.items():creator.add_metadata(key,value)
        creator.set_mainpath('A/course.html')
        tracks='<track src="../tracks/alias.vtt" srclang="en"><track src="missing.fr.vtt" srclang="fr">' if with_tracks else ''
        creator.add_item(Resource('A/course.html','text/html','<video><source src="../media/clip.'+extension+'">'+tracks+'</video><video src="https://example.invalid/remote.mp4"></video>'))
        creator.add_item(Resource('media/clip.'+extension,'video/'+extension,media or b'tiny media fixture, deliberately not decoded'))
        if with_tracks:
            creator.add_item(Resource('tracks/en.vtt','text/vtt','WEBVTT\n\n00:01.000 --> 00:02.000\nFictional 17 mm.\n'))
            creator.add_redirection('tracks/alias.vtt','Track alias','tracks/en.vtt',{})
        if media is None:creator.add_item(Resource('media/unlinked.mp4','video/mp4',b'orphan fixture'))
        if extra:creator.add_item(Resource('media/new.mp4','video/mp4',b'new fixture'))

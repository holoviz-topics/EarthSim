from dashboard import GrabCutApp, SelectRegionApp


if __name__ == '__main__':
    from bokeh.server.server import Server
    from app import shared_state

    server = Server({
        '/region': SelectRegionApp(name = 'Region Selection')(),
        '/grabcut': GrabCutApp(name='GrabCut Dashboard')()})

    server.start()

    server.io_loop.add_callback(server.show, "/region")
    server.io_loop.start()

else:
    print("Run dashboard using 'python launch.py'")

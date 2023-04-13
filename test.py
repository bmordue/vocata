from vocata.graph import get_graph

graph = get_graph()

subject = "https://vocatadev.pagekite.me/testcreate-priv"
actor = "https://vocatadev.pagekite.me/users/tester1"
target = "https://floss.social/users/Natureshadow/inbox"

res = graph.push_to(target, subject, actor)

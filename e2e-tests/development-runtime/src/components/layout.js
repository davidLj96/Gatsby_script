import React from "react"
import { StaticQuery, graphql, Slice } from "gatsby"

import Header from "./header"
import "./layout.css"

const Layout = ({ children }) => (
  <StaticQuery
    query={graphql`
      query SiteTitleQuery {
        site {
          siteMetadata {
            title
          }
        }
      }
    `}
    render={data => (
      <>
        <Header siteTitle={data.site.siteMetadata.title} />
        <div
          style={{
            margin: `0 auto`,
            maxWidth: 960,
            padding: `0px 1.0875rem 1.45rem`,
            paddingTop: 0,
          }}
        >
          {children}
        </div>
        <Slice alias="footer" framework="Gatsby" lang="js"/>

         {/** The slice below doesn't exist but it shouldn't break build */}
        <Slice alias="this-alias-does-not-exist" allowEmpty/>

         {/** Insert this here and expect it to fail   <Slice alias="this-alias-does-not-exist-too"/>*/}
      </>
    )}
  />
)

export default Layout
